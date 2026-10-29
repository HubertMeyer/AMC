using System.IO;
using System.Net.Sockets;
using System.Runtime.InteropServices;
using System.Security.Authentication;
using NAudio.MediaFoundation;
using NAudio.Wave;

namespace AccessibleMediaController.Windows.Services;

/// <summary>
/// Bezpośredni strumień radia przez własne połączenie ICY, tak jak robią to
/// foobar2000, VLC czy mpv: jedno połączenie z nagłówkiem Icy-MetaData daje
/// tytuły utworów (StreamTitle), a dźwięk MP3 albo AAC, także HE-AAC, dekodują
/// ramka po ramce systemowe dekodery Windows. Media Foundation otwierana
/// z adresu gra równie szybko, ale nigdy nie podaje StreamTitle, a podanie jej
/// całego strumienia czeka na bloki po 256 KB (około 10 s ciszy przy AAC).
/// </summary>
internal sealed class IcyFrameRadioWaveProvider : IWaveProvider, IRadioStreamTitleSource, IDisposable
{
    private const int NeedMoreInput = unchecked((int)0xC00D6D72); // MF_E_TRANSFORM_NEED_MORE_INPUT
    private const int StreamChange = unchecked((int)0xC00D6D61); // MF_E_TRANSFORM_STREAM_CHANGE
    private const int MaximumFramesWithoutAudio = 50;
    // Żywe serwery odpowiadają w ułamku sekundy; martwy adres nie może zjeść
    // czasu, który zostaje na dotychczasowe dekodery.
    private static readonly TimeSpan ConnectionTimeout = TimeSpan.FromSeconds(5);
    private static readonly Guid AacDecoder = new("32D186A7-218F-4C75-8876-DD77273A8999"); // CLSID_MSAACDecMFT
    private static readonly Guid Mp3Decoder = new("BBEEA841-0A63-4F52-A7AB-A9B3A84ED38A"); // CLSID_CMP3DecMediaObject

    private readonly LegacyIcyAudioStream _icy;
    private readonly Func<byte[]?> _nextFrame;
    private readonly object _gate = new();
    private IMFTransform? _decoder;
    private int _outputBufferSize;
    private bool _primed;
    private byte[] _pcm = new byte[256 * 1024];
    private int _pcmStart;
    private int _pcmEnd;

    private IcyFrameRadioWaveProvider(
        LegacyIcyAudioStream icy,
        string codec,
        Guid decoder,
        IMFMediaType inputType,
        Func<byte[]?> nextFrame)
    {
        _icy = icy;
        _nextFrame = nextFrame;
        Codec = codec;
        MediaFoundationApi.Startup();
        _decoder = (IMFTransform)Activator.CreateInstance(Type.GetTypeFromCLSID(decoder, throwOnError: true)!)!;
        _decoder.SetInputType(0, inputType, _MFT_SET_TYPE_FLAGS.None);
        WaveFormat = SelectOutputType(_decoder);
        _decoder.ProcessMessage(MFT_MESSAGE_TYPE.MFT_MESSAGE_NOTIFY_BEGIN_STREAMING, IntPtr.Zero);
        _decoder.ProcessMessage(MFT_MESSAGE_TYPE.MFT_MESSAGE_NOTIFY_START_OF_STREAM, IntPtr.Zero);
    }

    public string Codec { get; }
    public WaveFormat WaveFormat { get; private set; }
    public string? StreamTitle => _icy.StreamTitle;

    public event EventHandler<RadioStreamTitleChangedEventArgs>? StreamTitleChanged
    {
        add => _icy.StreamTitleChanged += value;
        remove => _icy.StreamTitleChanged -= value;
    }

    /// <summary>
    /// Zwraca null, gdy serwer nie nadaje MP3 ani AAC albo nie przyjmuje
    /// prostego połączenia; wtedy odtwarzacz próbuje dotychczasowych dekoderów.
    /// </summary>
    public static async Task<IcyFrameRadioWaveProvider?> TryOpenAsync(
        string source,
        CancellationToken cancellationToken)
    {
        LegacyIcyAudioStream? icy = null;
        IcyFrameRadioWaveProvider? provider = null;
        // Limit obejmuje całe otwarcie, także pierwszą ramkę i pierwsze
        // dekodowanie: zamknięcie gniazda przerywa każdy blokujący odczyt.
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        timeout.CancelAfter(ConnectionTimeout);
        using var closeOnTimeout = timeout.Token.Register(() => icy?.Dispose());
        try
        {
            icy = await LegacyIcyAudioStream.OpenAsync(source, timeout.Token).ConfigureAwait(false);
            if (icy.IsAac)
            {
                var frames = new AdtsFrameReader(icy);
                var first = frames.Next() ?? throw new EndOfStreamException("Stacja nie przesłała ramki AAC.");
                var inputType = AacInputType(first);
                provider = new IcyFrameRadioWaveProvider(icy, "AAC", AacDecoder, inputType, FirstThen([first.Data], () => frames.Next()?.Data));
                Marshal.ReleaseComObject(inputType);
            }
            else if (icy.IsMp3 && !string.IsNullOrWhiteSpace(icy.ContentType))
            {
                var stream = new FullReadStream(icy);
                var (first, second) = FirstMp3Frames(stream);
                var inputType = Mp3InputType(first);
                provider = new IcyFrameRadioWaveProvider(icy, "MP3", Mp3Decoder, inputType, FirstThen([first.RawData, second.RawData], () => Mp3Frame.LoadFromStream(stream)?.RawData));
                Marshal.ReleaseComObject(inputType);
            }
            else
            {
                icy.Dispose();
                return null;
            }

            // HE-AAC zmienia częstotliwość i kanały dopiero przy pierwszym
            // dekodowaniu; format musi być ostateczny, zanim odtwarzacz go odczyta.
            lock (provider._gate)
            {
                if (!provider.DecodeMore(provider._decoder!))
                    throw new EndOfStreamException("Stacja nie przesłała dźwięku.");
                provider._primed = true;
            }
            // Od teraz gniazdem rządzi odtwarzacz; limit otwarcia nie może go już zamknąć.
            closeOnTimeout.Dispose();
            if (timeout.IsCancellationRequested) throw new IOException("Stacja nie zdążyła się otworzyć.");
            return provider;
        }
        catch (Exception exception) when (!cancellationToken.IsCancellationRequested
            && exception is IOException
                or SocketException
                or ObjectDisposedException
                or InvalidDataException
                or NotSupportedException
                or ArgumentException
                or AuthenticationException
                or COMException
                or InvalidCastException
                or OperationCanceledException)
        {
            provider?.Dispose();
            icy?.Dispose();
            DiagnosticLog.Info(
                "radio",
                "Własne połączenie ICY nie zadziałało; próba pozostałych dekoderów "
                + $"({exception.GetType().Name}: {exception.Message}).");
            return null;
        }
        catch
        {
            provider?.Dispose();
            icy?.Dispose();
            cancellationToken.ThrowIfCancellationRequested();
            throw;
        }
    }

    public int Read(byte[] buffer, int offset, int count)
    {
        lock (_gate)
        {
            var decoder = _decoder ?? throw new ObjectDisposedException(nameof(IcyFrameRadioWaveProvider));
            while (_pcmEnd - _pcmStart < count && DecodeMore(decoder))
            {
            }
            var read = Math.Min(count, _pcmEnd - _pcmStart);
            read -= read % WaveFormat.BlockAlign;
            Buffer.BlockCopy(_pcm, _pcmStart, buffer, offset, read);
            _pcmStart += read;
            return read;
        }
    }

    public void Dispose()
    {
        // Najpierw gniazdo: odblokowuje Read czekający na sieć pod blokadą.
        _icy.Dispose();
        lock (_gate)
        {
            if (_decoder is null) return;
            try
            {
                _decoder.ProcessMessage(MFT_MESSAGE_TYPE.MFT_MESSAGE_NOTIFY_END_STREAMING, IntPtr.Zero);
            }
            catch (COMException)
            {
            }
            Marshal.ReleaseComObject(_decoder);
            _decoder = null;
        }
    }

    /// <summary>Dekoduje, aż w buforze pojawi się PCM. False na końcu strumienia.</summary>
    private bool DecodeMore(IMFTransform decoder)
    {
        for (var framesWithoutAudio = 0; ; framesWithoutAudio++)
        {
            if (DrainOutput(decoder)) return true;
            // Dekoder potrzebuje na start najwyżej kilku ramek. Dłuższe milczenie
            // znaczy, że odrzuca dane; odtwarzacz połączy się wtedy od nowa.
            if (framesWithoutAudio > MaximumFramesWithoutAudio)
                throw new InvalidDataException("Dekoder Windows nie zwraca dźwięku z tej stacji.");
            var frame = _nextFrame();
            if (frame is null) return false;
            var buffer = MediaFoundationApi.CreateMemoryBuffer(frame.Length);
            var sample = MediaFoundationApi.CreateSample();
            try
            {
                buffer.Lock(out var pointer, out _, out _);
                Marshal.Copy(frame, 0, pointer, frame.Length);
                buffer.Unlock();
                buffer.SetCurrentLength(frame.Length);
                sample.AddBuffer(buffer);
                decoder.ProcessInput(0, sample, 0);
            }
            finally
            {
                Marshal.ReleaseComObject(sample);
                Marshal.ReleaseComObject(buffer);
            }
        }
    }

    private bool DrainOutput(IMFTransform decoder)
    {
        var produced = false;
        while (true)
        {
            // Dekodery MP3 i AAC Windows nie przydzielają próbek wyjściowych.
            var sample = MediaFoundationApi.CreateSample();
            var buffer = MediaFoundationApi.CreateMemoryBuffer(_outputBufferSize);
            sample.AddBuffer(buffer);
            Marshal.ReleaseComObject(buffer);
            var outputs = new MFT_OUTPUT_DATA_BUFFER[] { new() { pSample = sample } };
            try
            {
                var result = decoder.ProcessOutput(_MFT_PROCESS_OUTPUT_FLAGS.None, 1, outputs, out _);
                if (result == NeedMoreInput) return produced;
                if (result == StreamChange)
                {
                    var format = SelectOutputType(decoder);
                    // Bufor odtwarzacza ma już stały format; nowy wymaga
                    // ponownego połączenia, które odtwarzacz robi sam.
                    if (_primed && !format.Equals(WaveFormat))
                        throw new InvalidDataException("Stacja zmieniła format dźwięku w trakcie nadawania.");
                    WaveFormat = format;
                    continue;
                }
                Marshal.ThrowExceptionForHR(result);
                sample.ConvertToContiguousBuffer(out var media);
                try
                {
                    media.GetCurrentLength(out var length);
                    if (length > 0)
                    {
                        media.Lock(out var pointer, out _, out _);
                        Append(pointer, length);
                        media.Unlock();
                        produced = true;
                    }
                }
                finally
                {
                    Marshal.ReleaseComObject(media);
                }
            }
            finally
            {
                // ProcessOutput oddaje tę samą próbkę drugi raz przez tablicę;
                // FinalRelease zwalnia oba odwzorowania naraz, około 40 razy na sekundę.
                Marshal.FinalReleaseComObject(sample);
                if (outputs[0].pEvents is not null) Marshal.ReleaseComObject(outputs[0].pEvents);
            }
        }
    }

    private void Append(IntPtr source, int length)
    {
        if (_pcmStart > 0 && _pcmEnd + length > _pcm.Length)
        {
            Buffer.BlockCopy(_pcm, _pcmStart, _pcm, 0, _pcmEnd - _pcmStart);
            _pcmEnd -= _pcmStart;
            _pcmStart = 0;
        }
        if (_pcmEnd + length > _pcm.Length) Array.Resize(ref _pcm, Math.Max(_pcm.Length * 2, _pcmEnd + length));
        Marshal.Copy(source, _pcm, _pcmEnd, length);
        _pcmEnd += length;
    }

    private WaveFormat SelectOutputType(IMFTransform decoder)
    {
        var types = new List<MediaType>();
        try
        {
            for (var index = 0; ; index++)
            {
                try
                {
                    decoder.GetOutputAvailableType(0, index, out var type);
                    types.Add(new MediaType(type));
                }
                catch (COMException)
                {
                    break;
                }
            }
            // Float jak w BASS: regulacja tempa pracuje na float bez przeliczania.
            var chosen = types.FirstOrDefault(type => type.SubType == AudioSubtypes.MFAudioFormat_Float)
                ?? types.FirstOrDefault(type => type.SubType == AudioSubtypes.MFAudioFormat_PCM)
                ?? throw new NotSupportedException("Dekoder Windows nie oferuje dźwięku PCM.");
            decoder.SetOutputType(0, chosen.MediaFoundationObject, _MFT_SET_TYPE_FLAGS.None);
            decoder.GetOutputStreamInfo(0, out var info);
            _outputBufferSize = Math.Max(info.cbSize, 64 * 1024);
            return chosen.SubType == AudioSubtypes.MFAudioFormat_Float
                ? WaveFormat.CreateIeeeFloatWaveFormat(chosen.SampleRate, chosen.ChannelCount)
                : new WaveFormat(chosen.SampleRate, chosen.BitsPerSample, chosen.ChannelCount);
        }
        finally
        {
            foreach (var type in types) Marshal.ReleaseComObject(type.MediaFoundationObject);
        }
    }

    private static Func<byte[]?> FirstThen(byte[][] first, Func<byte[]?> next)
    {
        var pending = new Queue<byte[]>(first);
        return () => pending.TryDequeue(out var frame) ? frame : next();
    }

    /// <summary>
    /// Strumień zaczyna się w środku danych i przypadkowe bajty potrafią udawać
    /// nagłówek MP3 o innej częstotliwości; dekoder Windows połyka wtedy po cichu
    /// wszystkie ramki. Przyjmujemy więc dopiero dwie kolejne ramki Layer III
    /// o tym samym formacie, jak przy ADTS.
    /// </summary>
    private static (Mp3Frame First, Mp3Frame Second) FirstMp3Frames(Stream stream)
    {
        var first = Mp3Frame.LoadFromStream(stream);
        for (var attempt = 0; first is not null && attempt < 64; attempt++)
        {
            var second = Mp3Frame.LoadFromStream(stream);
            if (second is null) break;
            if (first.MpegLayer == MpegLayer.Layer3
                && second.MpegLayer == MpegLayer.Layer3
                && first.SampleRate == second.SampleRate
                && first.ChannelMode == second.ChannelMode)
            {
                return (first, second);
            }
            first = second;
        }
        // Layer I/II (MP2) obsługuje dotychczasowa ścieżka Media Foundation.
        throw new InvalidDataException("Stacja nie nadaje rozpoznawalnych ramek MP3.");
    }

    private static IMFMediaType AacInputType(AdtsFrame first)
    {
        var type = MediaFoundationApi.CreateMediaType();
        type.SetGUID(MediaFoundationAttributes.MF_MT_MAJOR_TYPE, MediaTypes.MFMediaType_Audio);
        type.SetGUID(MediaFoundationAttributes.MF_MT_SUBTYPE, AudioSubtypes.MFAudioFormat_AAC);
        type.SetUINT32(MediaFoundationAttributes.MF_MT_AUDIO_SAMPLES_PER_SECOND, first.SampleRate);
        type.SetUINT32(MediaFoundationAttributes.MF_MT_AUDIO_NUM_CHANNELS, first.Channels);
        type.SetUINT32(MediaFoundationAttributes.MF_MT_AUDIO_BITS_PER_SAMPLE, 16);
        // ADTS: nagłówek zostaje na każdej ramce, więc dekoder nie potrzebuje
        // AudioSpecificConfig; MF_MT_USER_DATA to sam ogon HEAACWAVEINFO.
        type.SetUINT32(MediaFoundationAttributes.MF_MT_AAC_PAYLOAD_TYPE, 1);
        type.SetUINT32(MediaFoundationAttributes.MF_MT_AAC_AUDIO_PROFILE_LEVEL_INDICATION, 0xFE);
        byte[] userData = [1, 0, 0xFE, 0, 0, 0, 0, 0, 0, 0, 0, 0];
        type.SetBlob(MediaFoundationAttributes.MF_MT_USER_DATA, userData, userData.Length);
        return type;
    }

    private static IMFMediaType Mp3InputType(Mp3Frame first)
    {
        var type = MediaFoundationApi.CreateMediaType();
        type.SetGUID(MediaFoundationAttributes.MF_MT_MAJOR_TYPE, MediaTypes.MFMediaType_Audio);
        type.SetGUID(MediaFoundationAttributes.MF_MT_SUBTYPE, AudioSubtypes.MFAudioFormat_MP3);
        type.SetUINT32(MediaFoundationAttributes.MF_MT_AUDIO_SAMPLES_PER_SECOND, first.SampleRate);
        type.SetUINT32(MediaFoundationAttributes.MF_MT_AUDIO_NUM_CHANNELS, first.ChannelMode == ChannelMode.Mono ? 1 : 2);
        return type;
    }

    private readonly record struct AdtsFrame(byte[] Data, int SampleRate, int Channels);

    /// <summary>
    /// Dzieli strumień na ramki ADTS (synchronizacja 0xFFF, długość 13 bitów).
    /// Przed złapaniem rytmu wymaga synchronizacji także zaraz za ramką, bo
    /// strumień zaczyna się zwykle w połowie ramki, a 0xFFF trafia się w danych.
    /// </summary>
    private sealed class AdtsFrameReader(Stream stream)
    {
        private static readonly int[] SampleRates =
            [96000, 88200, 64000, 48000, 44100, 32000, 24000, 22050, 16000, 12000, 11025, 8000, 7350];
        private readonly byte[] _buffer = new byte[64 * 1024];
        private int _start;
        private int _end;
        private bool _locked;

        public AdtsFrame? Next()
        {
            while (true)
            {
                if (!Fill(7)) return null;
                var length = ((_buffer[_start + 3] & 3) << 11) | (_buffer[_start + 4] << 3) | (_buffer[_start + 5] >> 5);
                var samplingIndex = (_buffer[_start + 2] >> 2) & 0xF;
                if (!IsSync(_start) || length < 7 || samplingIndex >= SampleRates.Length)
                {
                    _start++;
                    _locked = false;
                    continue;
                }
                if (!Fill(_locked ? length : length + 2)) return null;
                if (!_locked && !IsSync(_start + length))
                {
                    _start++;
                    continue;
                }
                _locked = true;
                var data = _buffer.AsSpan(_start, length).ToArray();
                var channels = ((_buffer[_start + 2] & 1) << 2) | (_buffer[_start + 3] >> 6);
                _start += length;
                return new AdtsFrame(data, SampleRates[samplingIndex], channels);
            }
        }

        private bool IsSync(int index) => _buffer[index] == 0xFF && (_buffer[index + 1] & 0xF6) == 0xF0;

        private bool Fill(int count)
        {
            if (_end - _start >= count) return true;
            if (_start > 0)
            {
                Buffer.BlockCopy(_buffer, _start, _buffer, 0, _end - _start);
                _end -= _start;
                _start = 0;
            }
            while (_end - _start < count)
            {
                var read = stream.Read(_buffer, _end, _buffer.Length - _end);
                if (read <= 0) return false;
                _end += read;
            }
            return true;
        }
    }

    /// <summary>Mp3Frame czyta ciało ramki jednym Read; gniazdo oddaje dane kawałkami.</summary>
    private sealed class FullReadStream(Stream inner) : Stream
    {
        public override int Read(byte[] buffer, int offset, int count)
        {
            var total = 0;
            while (total < count)
            {
                var read = inner.Read(buffer, offset + total, count - total);
                if (read <= 0) break;
                total += read;
            }
            return total;
        }

        public override bool CanRead => true;
        public override bool CanSeek => false;
        public override bool CanWrite => false;
        public override long Length => throw new NotSupportedException();
        public override long Position { get => inner.Position; set => throw new NotSupportedException(); }
        public override void Flush() { }
        public override long Seek(long offset, SeekOrigin origin) => throw new NotSupportedException();
        public override void SetLength(long value) => throw new NotSupportedException();
        public override void Write(byte[] buffer, int offset, int count) => throw new NotSupportedException();
    }
}
