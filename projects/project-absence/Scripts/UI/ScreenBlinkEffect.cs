using System.Collections;
using UnityEngine;

/// <summary>
/// CanvasGroup 투명도를 바꿔 눈을 감았다 뜨는 효과를 표시합니다.
/// 자세한 수정 위치는 Documentation/01_코드와_수정안내.md를 참고하세요.
/// </summary>
[AddComponentMenu("결석/눈뜨기와 암전")]
public class ScreenBlinkEffect : MonoBehaviour
{
    [Header("화면 효과")]
    [SerializeField] private CanvasGroup blackOverlay;
    [SerializeField] private float closeDuration = 0.35f;
    [SerializeField] private float holdDuration = 0.25f;
    [SerializeField] private float openDuration = 0.8f;
    [SerializeField] private bool playOnStart = true;

    private void Start()
    {
        if (blackOverlay == null)
        {
            Debug.LogWarning("ScreenBlinkEffect: BlackOverlay를 연결해주세요.");
            return;
        }

        blackOverlay.alpha = 1f;
        blackOverlay.blocksRaycasts = true;

        if (playOnStart)
        {
            PlayBlink();
        }
    }

    public void PlayBlink()
    {
        if (blackOverlay == null)
        {
            return;
        }

        StopAllCoroutines();
        StartCoroutine(BlinkRoutine());
    }

    private IEnumerator BlinkRoutine()
    {
        blackOverlay.blocksRaycasts = true;
        yield return FadeTo(1f, closeDuration);
        yield return new WaitForSeconds(holdDuration);
        yield return FadeTo(0f, openDuration);
        blackOverlay.blocksRaycasts = false;
    }

    private IEnumerator FadeTo(float targetAlpha, float duration)
    {
        float startAlpha = blackOverlay.alpha;
        float elapsed = 0f;

        while (elapsed < duration)
        {
            elapsed += Time.deltaTime;
            blackOverlay.alpha = Mathf.Lerp(startAlpha, targetAlpha, elapsed / duration);
            yield return null;
        }

        blackOverlay.alpha = targetAlpha;
    }
}

