using UnityEngine;
using UnityEngine.InputSystem;

/// <summary>
/// 카메라 앞에서 가장 가까운 조사 대상을 찾고 E 입력을 전달합니다. 플레이어 자신의 충돌체는 제외합니다.
/// 자세한 수정 위치는 Documentation/01_코드와_수정안내.md를 참고하세요.
/// </summary>
[AddComponentMenu("결석/시선으로 조사하기")]
public class PlayerInteraction : MonoBehaviour
{
    [Header("상호작용")]
    [SerializeField] private Camera playerCamera;
    [SerializeField] private float interactionRange = 3f;
    [SerializeField] private KeyCode interactionKey = KeyCode.E;

    private IInteractable currentInteractable;
    private readonly RaycastHit[] interactionHits = new RaycastHit[32];
    public string CurrentInteractionText => currentInteractable?.InteractionText ?? "";

    private void Awake()
    {
        if (playerCamera == null)
        {
            playerCamera = Camera.main;
        }
    }

    private void Update()
    {
        if (playerCamera == null)
        {
            return;
        }

        if (GameStateManager.Instance != null && GameStateManager.Instance.QteActive)
        {
            return;
        }

        Ray ray = new Ray(playerCamera.transform.position, playerCamera.transform.forward);
        int count = Physics.RaycastNonAlloc(ray, interactionHits, interactionRange, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
        int closest = -1;
        float distance = float.PositiveInfinity;
        for (int i = 0; i < count; i++)
        {
            // 아래를 볼 때 카메라 앞에 들어오는 자신의 몸은 조사하지 않습니다.
            if (interactionHits[i].collider.transform.IsChildOf(transform)) continue;
            if (interactionHits[i].distance < distance) { closest = i; distance = interactionHits[i].distance; }
        }
        if (closest >= 0)
        {
            RaycastHit hit = interactionHits[closest];
            IInteractable interactable = hit.collider.GetComponentInParent<IInteractable>();

            if (interactable != null)
            {
                currentInteractable = interactable;

                if (InteractionPressed())
                {
                    interactable.TryInteract();
                }

                return;
            }
        }

        currentInteractable = null;
    }

    private bool InteractionPressed()
    {
        // 프로젝트는 새 Input System 전용 설정입니다. 기존 Inspector KeyCode 값은 유지합니다.
        if (Keyboard.current == null) return false;
        if (System.Enum.TryParse(interactionKey.ToString(), true, out Key key))
            return Keyboard.current[key].wasPressedThisFrame;
        return false;
    }

    private void OnDisable() { currentInteractable = null; }
}


