(() => {
  let music = null;
  let listenersInstalled = false;
  let requestVersion = 0;
  let itemId = '';
  let resourceId = '';

  const send = payload => window.chrome.webview.postMessage(payload);
  const errorText = error => String(error?.message || error || 'Nieznany błąd MusicKit');
  const player = () => music?.player || music;

  const stateName = state => {
    const states = window.MusicKit?.PlaybackStates || {};
    for (const [name, value] of Object.entries(states)) {
      if (value === state) return name;
    }
    return String(state ?? 'unknown');
  };

  const currentDuration = () => Number(
    player()?.currentPlaybackDuration
      ?? music?.nowPlayingItem?.playbackDuration
      ?? music?.nowPlayingItem?.attributes?.durationInMillis / 1000
      ?? 0);

  const currentPosition = () => Number(player()?.currentPlaybackTime ?? 0);

  const installListeners = () => {
    if (listenersInstalled || !music?.addEventListener) return;
    listenersInstalled = true;
    const events = window.MusicKit?.Events || {};
    const stateEvent = events.playbackStateDidChange || 'playbackStateDidChange';
    music.addEventListener(stateEvent, event => {
      const state = stateName(event?.state ?? player()?.playbackState);
      send({ type: 'state', requestVersion, itemId, resourceId, state });
      if (state.toLowerCase().includes('ended')) {
        send({ type: 'ended', requestVersion, itemId, resourceId });
      }
    });
  };

  const configure = async message => {
    const configured = await window.MusicKit.configure({
      developerToken: message.developerToken,
      app: { name: 'Accessible Multimedia Controller Test', build: message.build || 'test' }
    });
    music = configured || window.MusicKit.getInstance();
    if (message.musicUserToken) music.musicUserToken = message.musicUserToken;
    installListeners();
    send({ type: 'configured' });
  };

  const setQueue = async message => {
    const descriptor = message.resourceType === 'music-videos'
      ? { musicVideo: message.resourceId }
      : { song: message.resourceId };
    await music.setQueue(descriptor);
  };

  window.chrome.webview.addEventListener('message', async event => {
    const message = event.data || {};
    try {
      if (message.type === 'configure') {
        await configure(message);
        return;
      }
      if (!music) throw new Error('MusicKit nie jest skonfigurowany');
      if (message.type === 'authorize') {
        const token = await music.authorize();
        send({ type: 'authorized', musicUserToken: token || music.musicUserToken || '' });
        return;
      }
      if (message.type === 'unauthorize') {
        if (music.unauthorize) await music.unauthorize();
        send({ type: 'unauthorized' });
        return;
      }
      if (message.type === 'play') {
        requestVersion = Number(message.requestVersion || 0);
        itemId = String(message.itemId || '');
        resourceId = String(message.resourceId || '');
        await setQueue(message);
        music.volume = Math.max(0, Math.min(1, Number(message.volume || 0)));
        await music.play();
        if (Number(message.position) > 0 && player()?.seekToTime) {
          await player().seekToTime(Number(message.position));
        }
        send({ type: 'started', requestVersion, itemId, resourceId });
        return;
      }
      if (message.type === 'pause') await music.pause();
      if (message.type === 'stop') await music.stop();
      if (message.type === 'seek' && player()?.seekToTime) {
        await player().seekToTime(Math.max(0, Number(message.position || 0)));
      }
      if (message.type === 'volume') {
        music.volume = Math.max(0, Math.min(1, Number(message.volume || 0)));
      }
    } catch (error) {
      send({
        type: 'error',
        scope: message.type || 'unknown',
        requestVersion: Number(message.requestVersion || requestVersion || 0),
        itemId: String(message.itemId || itemId || ''),
        resourceId: String(message.resourceId || resourceId || ''),
        message: errorText(error)
      });
    }
  });

  setInterval(() => {
    if (!music || !itemId) return;
    send({
      type: 'progress', requestVersion, itemId, resourceId,
      position: currentPosition(), duration: currentDuration()
    });
  }, 500);

  const ready = () => send({ type: 'ready' });
  if (window.MusicKit) ready();
  else document.addEventListener('musickitloaded', ready, { once: true });
})();
