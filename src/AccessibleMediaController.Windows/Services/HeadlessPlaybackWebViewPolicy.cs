using Microsoft.Web.WebView2.Core;

namespace AccessibleMediaController.Windows.Services;

/// <summary>
/// Keeps the browser surfaces used only as audio engines out of keyboard and
/// screen-reader navigation. The TIDAL SDK creates two hidden video elements
/// for gapless playback; they are implementation details, not AMC controls.
/// </summary>
internal static class HeadlessPlaybackWebViewPolicy
{
    internal const string AccessibilityBootstrapScript = """
        (() => {
          const interactiveSelector =
            'audio, video, iframe, input, select, textarea, button, a[href], [tabindex], [contenteditable]';
          let observer;

          const releaseEngineFocus = node => {
            if (!(node instanceof HTMLElement)) return;
            if (document.activeElement === node) node.blur();
            setTimeout(() => {
              if (document.activeElement === node) node.blur();
            }, 0);
          };

          const hideEngineNode = node => {
            if (!(node instanceof Element)) return;
            if (node.matches(interactiveSelector)) {
              node.setAttribute('tabindex', '-1');
              node.setAttribute('aria-hidden', 'true');
              if (node instanceof HTMLMediaElement) node.controls = false;
              releaseEngineFocus(node);
            }
            node.querySelectorAll(interactiveSelector).forEach(hideEngineNode);
          };

          const observeDocument = () => {
            if (observer || !document.documentElement) return;
            observer = new MutationObserver(records => {
              for (const record of records) {
                for (const node of record.addedNodes) hideEngineNode(node);
              }
            });
            observer.observe(document.documentElement, { childList: true, subtree: true });
          };

          const configureDocument = () => {
            if (document.documentElement) {
              document.documentElement.setAttribute('aria-hidden', 'true');
              document.documentElement.setAttribute('tabindex', '-1');
              hideEngineNode(document.documentElement);
            }
            if (document.body) {
              document.body.setAttribute('aria-hidden', 'true');
              document.body.setAttribute('tabindex', '-1');
            }
            observeDocument();
          };

          document.addEventListener('DOMContentLoaded', configureDocument, { once: true });
          document.addEventListener('focusin', event => {
            releaseEngineFocus(event.target);
          }, true);
          configureDocument();
        })();
        """;

    internal static async Task ApplyAsync(CoreWebView2 coreWebView) =>
        _ = await coreWebView.AddScriptToExecuteOnDocumentCreatedAsync(
            AccessibilityBootstrapScript).ConfigureAwait(true);
}
