//! Adapter prędkości dla PCM z Librespota.
//!
//! Nie zmieniamy częstotliwości próbkowania (co podniosłoby lub obniżyło głos).
//! Te same przypięte silniki co w pozostałych sesjach AMC dostają stereo F32:
//! Speedy/Sonic dla odcinków mówionych i Signalsmith Stretch dla muzyki.

use std::ffi::c_void;
use std::os::windows::ffi::OsStrExt;
use std::path::{Path, PathBuf};
use std::ptr;
use std::sync::atomic::{AtomicBool, AtomicU32, AtomicU64, Ordering};
use std::sync::Arc;

use librespot_playback::audio_backend::{Sink, SinkError, SinkResult};
use librespot_playback::convert::Converter;
use librespot_playback::decoder::AudioPacket;
use windows_sys::Win32::Foundation::{FreeLibrary, HMODULE};
use windows_sys::Win32::System::LibraryLoader::{GetProcAddress, LoadLibraryW};

const SAMPLE_RATE: i32 = 44_100;
const CHANNELS: i32 = 2;
const ABI_VERSION: i32 = 1;
const ENGINE_SPEECH: i32 = 1;
const ENGINE_MUSIC: i32 = 2;
const OK: i32 = 0;
const READ_FRAMES: usize = 4096;

type AbiVersionFn = unsafe extern "C" fn() -> i32;
type CreateFn = unsafe extern "C" fn(i32, i32, i32, *mut i32) -> *mut c_void;
type DestroyFn = unsafe extern "C" fn(*mut c_void);
type SetTempoFn = unsafe extern "C" fn(*mut c_void, f32) -> i32;
type SetPitchFn = unsafe extern "C" fn(*mut c_void, f32) -> i32;
type WriteFn = unsafe extern "C" fn(*mut c_void, *const f32, i32) -> i32;
type ReadFn = unsafe extern "C" fn(*mut c_void, *mut f32, i32) -> i32;
type FlushFn = unsafe extern "C" fn(*mut c_void) -> i32;

#[derive(Clone)]
pub struct TempoControl {
    shared: Arc<TempoShared>,
}

struct TempoShared {
    rate_bits: AtomicU32,
    speech: AtomicBool,
    generation: AtomicU64,
    unavailable: Option<String>,
}

impl TempoControl {
    pub fn new() -> Self {
        let unavailable = TempoLibrary::probe().err();
        Self {
            shared: Arc::new(TempoShared {
                rate_bits: AtomicU32::new(1.0f32.to_bits()),
                speech: AtomicBool::new(false),
                generation: AtomicU64::new(0),
                unavailable,
            }),
        }
    }

    pub fn set_rate(&self, value: f32) -> Result<(), String> {
        if !(0.5..=2.0).contains(&value) || !value.is_finite() {
            return Err(
                "Prędkość Spotify musi mieścić się w zakresie 0,5 do 2,0 razy."
                    .to_string(),
            );
        }
        if (value - 1.0).abs() >= 0.001 {
            if let Some(reason) = &self.shared.unavailable {
                return Err(format!(
                    "Silnik zmiany prędkości Spotify jest niedostępny: {reason}"
                ));
            }
        }
        self.shared
            .rate_bits
            .store(value.to_bits(), Ordering::Release);
        Ok(())
    }

    pub fn begin_track(&self, speech: bool) {
        self.shared.speech.store(speech, Ordering::Release);
        self.reset_stream();
    }

    pub fn reset_stream(&self) {
        self.shared.generation.fetch_add(1, Ordering::AcqRel);
    }

    fn snapshot(&self) -> TempoSnapshot {
        TempoSnapshot {
            rate: f32::from_bits(self.shared.rate_bits.load(Ordering::Acquire)),
            speech: self.shared.speech.load(Ordering::Acquire),
            generation: self.shared.generation.load(Ordering::Acquire),
        }
    }
}

#[derive(Clone, Copy)]
struct TempoSnapshot {
    rate: f32,
    speech: bool,
    generation: u64,
}

pub struct TempoSink {
    inner: Box<dyn Sink>,
    control: TempoControl,
    processor: Option<NativeTempoStream>,
    generation: u64,
    speech: bool,
    rate: f32,
}

impl TempoSink {
    pub fn new(inner: Box<dyn Sink>, control: TempoControl) -> Self {
        let snapshot = control.snapshot();
        Self {
            inner,
            control,
            processor: None,
            generation: snapshot.generation,
            speech: snapshot.speech,
            rate: snapshot.rate,
        }
    }

    fn synchronize(&mut self, snapshot: TempoSnapshot) -> Result<(), String> {
        if self.generation != snapshot.generation || self.speech != snapshot.speech {
            self.processor = None;
            self.generation = snapshot.generation;
            self.speech = snapshot.speech;
        }
        if self.processor.is_none() && (snapshot.rate - 1.0).abs() >= 0.001 {
            self.processor = Some(NativeTempoStream::new(snapshot.speech, snapshot.rate)?);
        } else if let Some(processor) = self.processor.as_mut() {
            if (self.rate - snapshot.rate).abs() >= 0.001 {
                processor.set_rate(snapshot.rate)?;
            }
        }
        self.rate = snapshot.rate;
        Ok(())
    }

    fn finish_processor(&mut self, converter: &mut Converter) -> SinkResult<()> {
        let Some(mut processor) = self.processor.take() else {
            return Ok(());
        };
        let samples = processor
            .flush_and_drain()
            .map_err(SinkError::OnWrite)?;
        if !samples.is_empty() {
            self.inner
                .write(AudioPacket::Samples(samples), converter)?;
        }
        Ok(())
    }
}

impl Sink for TempoSink {
    fn start(&mut self) -> SinkResult<()> {
        self.inner.start()
    }

    fn stop(&mut self) -> SinkResult<()> {
        // Librespot wywołuje stop także przy pauzie. Wypychamy wyłącznie próbki,
        // które dekoder już przekazał, a po wznowieniu zaczynamy czysty strumień.
        let mut converter = Converter::new(None);
        self.finish_processor(&mut converter)?;
        self.inner.stop()
    }

    fn write(&mut self, packet: AudioPacket, converter: &mut Converter) -> SinkResult<()> {
        let snapshot = self.control.snapshot();
        self.synchronize(snapshot)
            .map_err(SinkError::NotConnected)?;
        let Some(processor) = self.processor.as_mut() else {
            return self.inner.write(packet, converter);
        };
        let samples = packet.samples().map_err(|error| {
            SinkError::InvalidParams(format!(
                "oczekiwano zdekodowanych próbek PCM: {error}"
            ))
        })?;
        if samples.len() % CHANNELS as usize != 0 {
            return Err(SinkError::InvalidParams(
                "pakiet PCM Spotify nie zawiera pełnych ramek stereo".to_string(),
            ));
        }
        let input: Vec<f32> = samples.iter().map(|sample| *sample as f32).collect();
        let output = processor
            .write_and_drain(&input)
            .map_err(SinkError::OnWrite)?;
        if output.is_empty() {
            return Ok(());
        }
        self.inner
            .write(AudioPacket::Samples(output), converter)
    }
}

struct TempoLibrary {
    module: HMODULE,
    create: CreateFn,
    destroy: DestroyFn,
    set_tempo: SetTempoFn,
    set_pitch: SetPitchFn,
    write: WriteFn,
    read: ReadFn,
    flush: FlushFn,
}

impl TempoLibrary {
    fn probe() -> Result<(), String> {
        let _ = Self::load()?;
        Ok(())
    }

    fn load() -> Result<Self, String> {
        let candidates = tempo_library_candidates();
        let mut failures = Vec::new();
        for path in candidates {
            match Self::load_from(&path) {
                Ok(library) => return Ok(library),
                Err(error) => failures.push(format!("{}: {error}", path.display())),
            }
        }
        Err(format!(
            "nie udało się wczytać AmcTempoEngines.dll ({})",
            failures.join("; ")
        ))
    }

    fn load_from(path: &Path) -> Result<Self, String> {
        let wide: Vec<u16> = path.as_os_str().encode_wide().chain(Some(0)).collect();
        let module = unsafe { LoadLibraryW(wide.as_ptr()) };
        if module.is_null() {
            return Err("LoadLibraryW odrzucił plik".to_string());
        }
        let result: Result<Self, String> = (|| unsafe {
            let abi: AbiVersionFn = symbol(module, b"AmcTempoAbiVersion\0")?;
            if abi() != ABI_VERSION {
                return Err("niezgodna wersja ABI".to_string());
            }
            Ok(Self {
                module,
                create: symbol(module, b"AmcTempoCreate\0")?,
                destroy: symbol(module, b"AmcTempoDestroy\0")?,
                set_tempo: symbol(module, b"AmcTempoSetTempo\0")?,
                set_pitch: symbol(module, b"AmcTempoSetPitch\0")?,
                write: symbol(module, b"AmcTempoWrite\0")?,
                read: symbol(module, b"AmcTempoRead\0")?,
                flush: symbol(module, b"AmcTempoFlush\0")?,
            })
        })();
        if result.is_err() {
            unsafe {
                FreeLibrary(module);
            }
        }
        result
    }
}

unsafe fn symbol<T: Copy>(module: HMODULE, name: &[u8]) -> Result<T, String> {
    let address = GetProcAddress(module, name.as_ptr());
    let Some(address) = address else {
        let label = String::from_utf8_lossy(&name[..name.len().saturating_sub(1)]);
        return Err(format!("brak funkcji {label}"));
    };
    Ok(std::mem::transmute_copy(&address))
}

impl Drop for TempoLibrary {
    fn drop(&mut self) {
        if !self.module.is_null() {
            unsafe {
                FreeLibrary(self.module);
            }
            self.module = ptr::null_mut();
        }
    }
}

struct NativeTempoStream {
    library: TempoLibrary,
    handle: *mut c_void,
    read_buffer: Vec<f32>,
}

impl NativeTempoStream {
    fn new(speech: bool, rate: f32) -> Result<Self, String> {
        let library = TempoLibrary::load()?;
        Self::with_library(library, speech, rate)
    }

    fn with_library(library: TempoLibrary, speech: bool, rate: f32) -> Result<Self, String> {
        let mut status = 0;
        let engine = if speech {
            ENGINE_SPEECH
        } else {
            ENGINE_MUSIC
        };
        let handle = unsafe {
            (library.create)(engine, SAMPLE_RATE, CHANNELS, &mut status)
        };
        if handle.is_null() || status != OK {
            return Err(format!(
                "nie udało się utworzyć silnika tempa (kod {status})"
            ));
        }
        let mut stream = Self {
            library,
            handle,
            read_buffer: vec![0.0; READ_FRAMES * CHANNELS as usize],
        };
        stream.set_rate(rate)?;
        let pitch = unsafe {
            (stream.library.set_pitch)(stream.handle, 1.0)
        };
        if pitch != OK {
            return Err(format!(
                "silnik tempa odrzucił zachowanie wysokości głosu (kod {pitch})"
            ));
        }
        Ok(stream)
    }

    fn set_rate(&mut self, rate: f32) -> Result<(), String> {
        let status = unsafe {
            (self.library.set_tempo)(self.handle, rate)
        };
        if status == OK {
            Ok(())
        } else {
            Err(format!(
                "silnik tempa odrzucił prędkość {rate} (kod {status})"
            ))
        }
    }

    fn write_and_drain(&mut self, input: &[f32]) -> Result<Vec<f64>, String> {
        let frames = input.len() / CHANNELS as usize;
        let accepted = unsafe {
            (self.library.write)(self.handle, input.as_ptr(), frames as i32)
        };
        if accepted != frames as i32 {
            return Err(format!(
                "silnik tempa nie przyjął całego pakietu ({accepted}/{frames})"
            ));
        }
        self.drain()
    }

    fn flush_and_drain(&mut self) -> Result<Vec<f64>, String> {
        let status = unsafe {
            (self.library.flush)(self.handle)
        };
        if status != OK {
            return Err(format!(
                "silnik tempa nie domknął strumienia (kod {status})"
            ));
        }
        self.drain()
    }

    fn drain(&mut self) -> Result<Vec<f64>, String> {
        let mut output = Vec::new();
        loop {
            let frames = unsafe {
                (self.library.read)(
                    self.handle,
                    self.read_buffer.as_mut_ptr(),
                    READ_FRAMES as i32,
                )
            };
            if frames < 0 {
                return Err(format!(
                    "silnik tempa zwrócił błąd odczytu {frames}"
                ));
            }
            if frames == 0 {
                break;
            }
            let samples = frames as usize * CHANNELS as usize;
            output.extend(
                self.read_buffer[..samples]
                    .iter()
                    .map(|sample| *sample as f64),
            );
        }
        Ok(output)
    }
}

impl Drop for NativeTempoStream {
    fn drop(&mut self) {
        if !self.handle.is_null() {
            unsafe {
                (self.library.destroy)(self.handle);
            }
            self.handle = ptr::null_mut();
        }
    }
}

fn tempo_library_candidates() -> Vec<PathBuf> {
    let mut candidates = Vec::new();
    if let Ok(executable) = std::env::current_exe() {
        if let Some(folder) = executable.parent() {
            candidates.push(folder.join("AmcTempoEngines.dll"));
            if let Some(parent) = folder.parent() {
                candidates.push(parent.join("AmcTempoEngines.dll"));
            }
        }
    }
    candidates
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn candidate_paths_cover_packaged_parent_folder() {
        let candidates = tempo_library_candidates();
        assert!(candidates.iter().any(|path| {
            path.file_name().and_then(|name| name.to_str())
                == Some("AmcTempoEngines.dll")
        }));
        assert!(candidates.len() >= 2);
    }

    #[test]
    fn bundled_library_matches_expected_abi() {
        let path = bundled_library_path();
        let library = TempoLibrary::load_from(&path)
            .unwrap_or_else(|error| panic!("{}: {error}", path.display()));
        drop(library);
    }

    #[test]
    fn bundled_engines_change_duration_without_resampling() {
        let input_frames = SAMPLE_RATE as usize;
        let input: Vec<f32> = (0..input_frames)
            .flat_map(|frame| {
                let sample = ((frame as f32 / SAMPLE_RATE as f32) * 440.0 * std::f32::consts::TAU)
                    .sin()
                    * 0.1;
                [sample, sample]
            })
            .collect();

        for speech in [true, false] {
            let library = TempoLibrary::load_from(&bundled_library_path()).unwrap();
            let mut stream = NativeTempoStream::with_library(library, speech, 1.5).unwrap();
            let mut output = stream.write_and_drain(&input).unwrap();
            output.extend(stream.flush_and_drain().unwrap());

            let output_frames = output.len() / CHANNELS as usize;
            assert!(
                output_frames > input_frames / 2,
                "silnik {speech} skrócił sygnał zbyt mocno: {output_frames} ramek"
            );
            assert!(
                output_frames < input_frames,
                "silnik {speech} nie przyspieszył sygnału: {output_frames} ramek"
            );
        }
    }

    #[test]
    fn control_keeps_rate_kind_and_reset_generation_separate() {
        let control = TempoControl::new();
        let before = control.snapshot();
        control.begin_track(true);
        let after = control.snapshot();
        assert!(after.speech);
        assert!(after.generation > before.generation);
        assert_eq!(after.rate, 1.0);
    }

    fn bundled_library_path() -> PathBuf {
        Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("../../third_party/AmcTempoEngines/win-x64/AmcTempoEngines.dll")
    }
}
