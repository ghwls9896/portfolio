using System.Collections;
using UnityEngine;
using UnityEngine.InputSystem;

/// <summary>
/// 눈뜨기 → 의사 대화 → 의사 퇴장 → 휴식 → 자유 탐색의 순서와 카메라 전환을 관리합니다.
/// 자세한 수정 위치는 Documentation/01_코드와_수정안내.md를 참고하세요.
/// </summary>
[AddComponentMenu("결석/병실 도입 순서")]
public class HospitalIntroSequence : MonoBehaviour
{
    public enum IntroStage { Waking, Dialogue, DoctorLeaving, Resting, Exploring }
    [System.Serializable] public class DialogueLine
    {
        public string speaker = "의사";
        [TextArea(2, 4)] public string text;
    }
    public Camera hospitalIntroCamera;
    public GameObject player;
    public Transform playerStandPoint;
    public HospitalDialogueUI dialogueUI;
    public HospitalDoctorExit doctor;
    public CanvasGroup blackOverlay;
    public ScreenBlinkEffect blinkEffect;
    public PlayerInteraction interaction;
    public DialogueLine[] lines;
    public IntroStage Stage { get; private set; }

    private IEnumerator Start()
    {
        if (!hospitalIntroCamera || !player || !dialogueUI || !doctor || !blackOverlay || !playerStandPoint)
        {
            Debug.LogError("HospitalIntroSequence: Inspector의 필수 연결을 확인해주세요.", this);
            yield break;
        }
        Stage = IntroStage.Waking;
        player.SetActive(false);
        hospitalIntroCamera.gameObject.SetActive(true);
        dialogueUI.HideDialogue();
        dialogueUI.hintText.text = "";
        blackOverlay.alpha = 1;
        Cursor.lockState = CursorLockMode.None;
        Cursor.visible = false;
        if (GameStateManager.Instance) GameStateManager.Instance.SetDay(GameDay.Day0);
        yield return new WaitForSeconds(1.8f);
        if (blinkEffect) blinkEffect.PlayBlink();
        else yield return Fade(0, 2.5f);
        yield return new WaitForSeconds(3.6f);
        dialogueUI.chapterText.text = "DAY 0   /   병실";
        yield return new WaitForSeconds(1.8f);
        dialogueUI.chapterText.text = "";
        Stage = IntroStage.Dialogue;
        foreach (var line in lines) yield return dialogueUI.Say(line.speaker, line.text);
        dialogueUI.HideDialogue();
        Stage = IntroStage.DoctorLeaving;
        yield return doctor.LeaveRoom();
        Stage = IntroStage.Resting;
        dialogueUI.hintText.text = "E  ·  천천히 일어나기";
        while (Keyboard.current == null || !Keyboard.current.eKey.wasPressedThisFrame) yield return null;
        dialogueUI.hintText.text = "";
        yield return Fade(1, 0.65f);
        hospitalIntroCamera.gameObject.SetActive(false);
        player.transform.SetPositionAndRotation(playerStandPoint.position, playerStandPoint.rotation);
        var movement = player.GetComponent<FirstPersonController>();
        if (movement) movement.enabled = false;
        if (interaction) interaction.enabled = false;
        player.SetActive(true);
        yield return Fade(0, 1.2f);
        Stage = IntroStage.Exploring;
        if (movement) movement.enabled = true;
        if (interaction) interaction.enabled = true;
        dialogueUI.ShowObservation("낯선 병실이다. 잠깐 주변을 살펴보자.");
    }

    private void Update()
    {
        if (Stage != IntroStage.Exploring || !dialogueUI || dialogueUI.IsBusy) return;
        string prompt = interaction ? interaction.CurrentInteractionText : "";
        dialogueUI.hintText.text = string.IsNullOrEmpty(prompt)
            ? "W A S D  이동    ·    마우스  둘러보기    ·    ESC  커서 해제"
            : "E  ·  " + prompt;
    }

    private IEnumerator Fade(float target, float duration)
    {
        float start = blackOverlay.alpha;
        for (float t = 0; t < 1; t += Time.deltaTime / duration)
        {
            blackOverlay.alpha = Mathf.Lerp(start, target, t);
            yield return null;
        }
        blackOverlay.alpha = target;
    }

    private void OnDisable()
    {
        Cursor.lockState = CursorLockMode.None;
        Cursor.visible = true;
    }

#if UNITY_EDITOR
    // Editor 검사 전용 진입점. 일반 Play에서는 병원 도입부가 그대로 진행됩니다.
    public void BeginExplorationPreview()
    {
        StopAllCoroutines();
        if (blinkEffect) blinkEffect.StopAllCoroutines();
        blackOverlay.alpha = 0; dialogueUI.HideDialogue(); dialogueUI.chapterText.text = "";
        hospitalIntroCamera.gameObject.SetActive(false);
        doctor.gameObject.SetActive(false);
        if (doctor.corridorPresence) doctor.corridorPresence.SetActive(true);
        player.transform.SetPositionAndRotation(playerStandPoint.position, playerStandPoint.rotation);
        player.SetActive(true);
        player.GetComponent<FirstPersonController>().enabled = true; interaction.enabled = true;
        Stage = IntroStage.Exploring;
    }
#endif
}

