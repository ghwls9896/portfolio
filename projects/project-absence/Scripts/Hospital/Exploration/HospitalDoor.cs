using System.Collections;
using UnityEngine;

/// <summary>
/// 경첩 회전으로 문을 여닫고 병실 도입 또는 시설관리 출입 조건을 확인합니다.
/// 자세한 수정 위치는 Documentation/01_코드와_수정안내.md를 참고하세요.
/// </summary>
[AddComponentMenu("결석/열고 닫는 문")]
public class HospitalDoor : MonoBehaviour, IInteractable
{
    public Transform hinge;
    public float openAngle = 95;
    public HospitalIntroSequence intro;
    public bool requireExploration;
    public HospitalAreaProgress access;
    public bool requireServiceAccess;
    public HospitalDialogueUI ui;
    public AudioSource latchAudio;
    private bool moving;
    private Quaternion closedRotation;
    private void Awake() { closedRotation = hinge.localRotation; }
    public bool IsOpen { get; private set; }
    public string InteractionText => moving ? "" : IsOpen ? "문을 닫는다" : "문을 연다";
    public bool TryInteract()
    {
        if (moving || (ui && ui.IsBusy)) return false;
        if (requireExploration && intro && intro.Stage != HospitalIntroSequence.IntroStage.Exploring) return false;
        if (requireServiceAccess && access && !access.ServiceAccessUnlocked)
        { ui.ShowObservation("관리용 출입문이다. 옆의 패널에 표시등이 켜져 있다."); return false; }
        StartCoroutine(Toggle()); return true;
    }
    private IEnumerator Toggle()
    {
        moving = true;
        Quaternion start = hinge.localRotation;
        Quaternion end = closedRotation * Quaternion.Euler(0, IsOpen ? 0 : openAngle, 0);
        if (latchAudio) latchAudio.Play();
        for (float t = 0; t < 1; t += Time.deltaTime / .8f)
        { hinge.localRotation = Quaternion.Slerp(start, end, Mathf.SmoothStep(0, 1, t)); yield return null; }
        hinge.localRotation = end; IsOpen = !IsOpen; moving = false;
    }
}

