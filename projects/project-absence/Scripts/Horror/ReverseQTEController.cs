using UnityEngine;
using UnityEngine.InputSystem;

/// <summary>
/// 연타 성공은 저항, 취소 또는 시간 만료는 저항하지 않음으로 기록하여 엔딩 판정을 요청합니다.
/// 자세한 수정 위치는 Documentation/01_코드와_수정안내.md를 참고하세요.
/// </summary>
[AddComponentMenu("결석/엄마 QTE 분기")]
public class ReverseQTEController : MonoBehaviour
{
    [Header("역 QTE")]
    [SerializeField] private KeyCode qteKey = KeyCode.Space;
    [SerializeField] private int requiredPresses = 12;
    [SerializeField] private float timeoutSeconds = 2.5f;

    private bool active;
    private int currentPresses;
    private float startTime;

    public void StartQTE()
    {
        active = true;
        currentPresses = 0;
        startTime = Time.time;

        if (GameStateManager.Instance != null)
        {
            GameStateManager.Instance.StartQTE();
        }
    }

    private void Update()
    {
        if (!active)
        {
            return;
        }

        if (Keyboard.current != null && Keyboard.current.escapeKey.wasPressedThisFrame)
        {
            CancelQTE();
            return;
        }

        if (Keyboard.current != null && System.Enum.TryParse(qteKey.ToString(), true, out Key key) && Keyboard.current[key].wasPressedThisFrame)
        {
            currentPresses++;
            Debug.Log($"SPACE 입력: {currentPresses}/{requiredPresses}");

            if (currentPresses >= requiredPresses)
            {
                CompleteQTE(true);
                return;
            }
        }

        if (Time.time - startTime >= timeoutSeconds)
        {
            CompleteQTE(false);
        }
    }

    private void CompleteQTE(bool resisted)
    {
        active = false;

        if (GameStateManager.Instance != null)
        {
            GameStateManager.Instance.SetMotherResisted(resisted);
            GameStateManager.Instance.FinishQTE();
            GameStateManager.Instance.EndGame();
        }

        Debug.Log($"QTE 결과: {(resisted ? "저항 성공" : "저항 실패")} / 엔딩: {GameStateManager.Instance?.ResolveEnding()}");
    }

    public void CancelQTE()
    {
        if (active) CompleteQTE(false);
    }
}

