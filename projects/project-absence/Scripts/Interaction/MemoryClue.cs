using UnityEngine;
using UnityEngine.Events;

/// <summary>
/// 단서 중복 획득을 막고 자각도 점수와 Inspector의 획득 이벤트를 전달합니다.
/// 자세한 수정 위치는 Documentation/01_코드와_수정안내.md를 참고하세요.
/// </summary>
[AddComponentMenu("결석/한 번만 얻는 단서")]
public class MemoryClue : MonoBehaviour, IInteractable
{
    [Header("단서")]
    [SerializeField] private string clueId = "M01";
    [SerializeField] private int memoryValue = 1;
    [SerializeField] private string interactionText = "단서를 조사한다.";
    [SerializeField] private bool collected;
    [SerializeField] private bool hideAfterCollection = true;
    public UnityEvent onCollected = new UnityEvent();

    public string InteractionText => collected ? "" : interactionText;

    public bool TryInteract()
    {
        if (collected)
        {
            return false;
        }

        collected = true;

        if (GameStateManager.Instance != null)
        {
            GameStateManager.Instance.AddMemory(memoryValue);
        }

        Debug.Log($"단서 획득: {clueId} (+{memoryValue})");
        onCollected.Invoke();
        if (hideAfterCollection) gameObject.SetActive(false);
        return true;
    }
}

