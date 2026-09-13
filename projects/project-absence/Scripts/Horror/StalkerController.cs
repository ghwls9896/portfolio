using UnityEngine;

/// <summary>
/// 지정한 대상을 향해 이동하는 기본 추적 컴포넌트입니다. 병원 NPC 대화와는 별개입니다.
/// 자세한 수정 위치는 Documentation/01_코드와_수정안내.md를 참고하세요.
/// </summary>
[AddComponentMenu("결석/추적자 기본 이동")]
public class StalkerController : MonoBehaviour
{
    [Header("스토커")]
    [SerializeField] private Transform target;
    [SerializeField] private float moveSpeed = 1.8f;
    [SerializeField] private float activateDistance = 12f;
    [SerializeField] private float stopDistance = 1.4f;
    [SerializeField] private bool active;

    public void SetTarget(Transform newTarget)
    {
        target = newTarget;
    }

    public void SetActive(bool value)
    {
        active = value;
    }

    private void Update()
    {
        if (!active || target == null)
        {
            return;
        }

        Vector3 direction = target.position - transform.position;
        float distance = direction.magnitude;

        if (distance <= activateDistance)
        {
            direction = direction.normalized;

            if (distance > stopDistance)
            {
                transform.position += direction * moveSpeed * Time.deltaTime;
            }
        }
    }
}

