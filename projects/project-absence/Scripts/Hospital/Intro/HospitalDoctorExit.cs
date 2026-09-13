using System.Collections;
using UnityEngine;

// 작은 병실의 고정 퇴장 동선입니다. NavMesh 없이 Inspector의 경유점을 따라갑니다.
/// <summary>
/// 경유점을 따라 의사를 이동시키고 병실 문을 여닫은 뒤 복도 의사를 활성화합니다.
/// 자세한 수정 위치는 Documentation/01_코드와_수정안내.md를 참고하세요.
/// </summary>
[AddComponentMenu("결석/의사 퇴장 동선")]
public class HospitalDoctorExit : MonoBehaviour
{
    public Transform[] exitWaypoints;
    public Transform doorPivot;
    public AudioSource footsteps;
    public AudioSource doorSound;
    public float walkSpeed = 0.85f;
    public float turnSpeed = 160f;
    public Animator animator;
    public GameObject corridorPresence;
    public Transform leftLeg, rightLeg, leftArm, rightArm;
    private Quaternion leftLegRest, rightLegRest, leftArmRest, rightArmRest;
    private float stride;

    public IEnumerator LeaveRoom()
    {
        if (animator != null) animator.enabled = false;
        if (leftLeg) leftLegRest = leftLeg.localRotation;
        if (rightLeg) rightLegRest = rightLeg.localRotation;
        if (leftArm) leftArmRest = leftArm.localRotation;
        if (rightArm) rightArmRest = rightArm.localRotation;
        Quaternion closed = doorPivot ? doorPivot.localRotation : Quaternion.identity;
        for (int i = 0; i < exitWaypoints.Length; i++)
        {
            // 문 바로 앞에서 문을 열고, 문턱을 지난 후 복도 쪽으로 꺾습니다.
            if (i == 2 && doorPivot) yield return RotateDoor(closed * Quaternion.Euler(0, 95, 0));
            Vector3 goal = exitWaypoints[i].position;
            while (Vector3.Distance(transform.position, goal) > 0.025f)
            {
                Vector3 direction = goal - transform.position;
                direction.y = 0;
                Quaternion facing = Quaternion.LookRotation(direction);
                transform.rotation = Quaternion.RotateTowards(transform.rotation, facing, turnSpeed * Time.deltaTime);
                if (Quaternion.Angle(transform.rotation, facing) < 30)
                {
                    transform.position = Vector3.MoveTowards(transform.position, goal, walkSpeed * Time.deltaTime);
                    AnimateStep();
                }
                yield return null;
            }
        }
        if (doorPivot) yield return RotateDoor(closed);
        if (corridorPresence) corridorPresence.SetActive(true);
        gameObject.SetActive(false);
    }

    private void AnimateStep()
    {
        float previous = stride;
        stride += Time.deltaTime * 7f;
        float swing = Mathf.Sin(stride);
        if (leftLeg) leftLeg.localRotation = leftLegRest * Quaternion.Euler(20 * swing, 0, 0);
        if (rightLeg) rightLeg.localRotation = rightLegRest * Quaternion.Euler(-20 * swing, 0, 0);
        if (leftArm) leftArm.localRotation = leftArmRest * Quaternion.Euler(-7 * swing, 0, 0);
        if (rightArm) rightArm.localRotation = rightArmRest * Quaternion.Euler(7 * swing, 0, 0);
        if ((int)(previous / Mathf.PI) != (int)(stride / Mathf.PI) && footsteps) footsteps.Play();
    }

    private IEnumerator RotateDoor(Quaternion target)
    {
        if (doorSound) doorSound.Play();
        Quaternion start = doorPivot.localRotation;
        for (float t = 0; t < 1; t += Time.deltaTime / 1.1f)
        {
            doorPivot.localRotation = Quaternion.Slerp(start, target, Mathf.SmoothStep(0, 1, t));
            yield return null;
        }
        doorPivot.localRotation = target;
    }
}

