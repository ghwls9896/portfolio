using System.Collections;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.InputSystem;

/// <summary>
/// 추락 기록과 암전을 실행합니다. 엔딩 결과는 미정이며 R 복귀는 프로토타입 검토용입니다.
/// 자세한 수정 위치는 Documentation/01_코드와_수정안내.md를 참고하세요.
/// </summary>
[AddComponentMenu("결석/옥상 추락 이벤트")]
public class HospitalRoofFall : MonoBehaviour
{
    public HospitalIntroSequence intro;
    public Transform roofReturnPoint;
    public UnityEvent onRoofFall = new UnityEvent();
    public bool HasFallen { get; private set; }
    private void OnTriggerEnter(Collider other)
    {
        if (!HasFallen && other.GetComponentInParent<FirstPersonController>()) StartCoroutine(Fall());
    }
    private IEnumerator Fall()
    {
        HasFallen = true;
        var movement = intro.player.GetComponent<FirstPersonController>();
        intro.dialogueUI.BeginModal(movement, intro.interaction);
        GameStateManager.Instance?.RecordDayZeroRoofFall();
        onRoofFall.Invoke(); // 결과가 결정되면 이 이벤트에 후속 연출을 연결합니다.
        for (float t = 0; t < 1; t += Time.deltaTime / .75f)
        { intro.blackOverlay.alpha = t; yield return null; }
        intro.blackOverlay.alpha = 1;
        intro.dialogueUI.hintText.text = "";
        // 엔딩 판정 없이 사건만 종료합니다. 검토용 재시작 입력은 암전 위에 표시합니다.
        yield return new WaitForSeconds(1);
        intro.dialogueUI.chapterText.transform.SetAsLastSibling();
        intro.dialogueUI.chapterText.text = "R  ·  다시 시도";
        while (Keyboard.current == null || !Keyboard.current.rKey.wasPressedThisFrame) yield return null;
        var controller = intro.player.GetComponent<CharacterController>(); controller.enabled = false;
        intro.player.transform.SetPositionAndRotation(roofReturnPoint.position, roofReturnPoint.rotation);
        movement.ResetMotion(); controller.enabled = true;
        intro.dialogueUI.chapterText.text = "";
        intro.blackOverlay.alpha = 0; intro.dialogueUI.EndModal(); HasFallen = false;
    }
}

