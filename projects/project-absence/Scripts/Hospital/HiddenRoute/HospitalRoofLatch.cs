using System.Collections;
using UnityEngine;
using UnityEngine.InputSystem;

/// <summary>
/// E를 놓았다가 계속 누르는 시간을 측정합니다. 중간에 놓으면 진행이 초기화되고 ESC로 취소합니다.
/// 자세한 수정 위치는 Documentation/01_코드와_수정안내.md를 참고하세요.
/// </summary>
[AddComponentMenu("결석/옥상 걸쇠 연속 입력")]
public class HospitalRoofLatch : MonoBehaviour, IInteractable
{
    public Transform gate;
    public HospitalAreaProgress progress;
    public HospitalDialogueUI ui;
    public FirstPersonController movement;
    public PlayerInteraction interaction;
    public float holdSeconds = 4;
    public bool IsReleased { get; private set; }
    public float HoldProgress { get; private set; }
    private bool working;
    public string InteractionText => IsReleased ? "" : "고착된 걸쇠를 살펴본다";
    public bool TryInteract()
    {
        if (IsReleased || working || !progress.ServiceAccessUnlocked || !ui.BeginModal(movement, interaction)) return false;
        StartCoroutine(Release()); return true;
    }
    private IEnumerator Release()
    {
        working = true;
        ui.hintText.text = "E를 놓은 뒤 길게 누르기   ·   ESC 돌아가기";
        yield return null;
        while (Keyboard.current != null && Keyboard.current.eKey.isPressed) yield return null;
        float held = 0;
        while (held < holdSeconds)
        {
            var k = Keyboard.current;
            if (k != null && k.escapeKey.wasPressedThisFrame) { working = false; ui.EndModal(); yield break; }
            held = k != null && k.eKey.isPressed ? held + Time.deltaTime : 0;
            HoldProgress = held / holdSeconds;
            ui.hintText.text = "E 길게 누르기  " + new string('▰', Mathf.FloorToInt(HoldProgress * 8)) + new string('▱', 8 - Mathf.FloorToInt(HoldProgress * 8)) + "   ·   ESC 돌아가기";
            yield return null;
        }
        var start = gate.localRotation;
        var target = start * Quaternion.Euler(0, 100, 0);
        for (float t = 0; t < 1; t += Time.deltaTime)
        { gate.localRotation = Quaternion.Slerp(start, target, t); yield return null; }
        gate.localRotation = target; IsReleased = true; working = false;
        ui.EndModal(); ui.ShowObservation("걸쇠가 풀렸다. 바깥에서 바람이 밀려온다.");
    }
    private void OnDisable() { if (working) { StopAllCoroutines(); working = false; ui.EndModal(); } }
}

