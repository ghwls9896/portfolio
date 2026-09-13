using System.Collections;
using UnityEngine;
using UnityEngine.Events;

/// <summary>
/// 첫 대화와 반복 대사를 표시하고 첫 대화 완료 이벤트를 한 번 호출합니다.
/// 자세한 수정 위치는 Documentation/01_코드와_수정안내.md를 참고하세요.
/// </summary>
[AddComponentMenu("결석/NPC 대화 내용")]
public class HospitalNpcConversation : MonoBehaviour, IInteractable
{
    public string speakerName;
    [TextArea(2, 4)] public string[] firstConversation;
    [TextArea(2, 4)] public string[] repeatConversation;
    public HospitalDialogueUI ui;
    public FirstPersonController movement;
    public PlayerInteraction interaction;
    public UnityEvent onFirstConversation = new UnityEvent();
    public bool HasSpoken { get; private set; }
    private bool talking;
    public string InteractionText => ui && !ui.IsBusy ? speakerName + "에게 말을 건다" : "";

    public bool TryInteract()
    {
        if (talking || !ui || !ui.BeginModal(movement, interaction)) return false;
        StartCoroutine(Talk()); return true;
    }
    private IEnumerator Talk()
    {
        talking = true;
        try
        {
            var lines = HasSpoken ? repeatConversation : firstConversation;
            foreach (string line in lines) yield return ui.Say(speakerName, line);
            if (!HasSpoken) { HasSpoken = true; onFirstConversation.Invoke(); }
        }
        finally { talking = false; ui.EndModal(); }
    }
    private void OnDisable()
    {
        if (talking) { StopAllCoroutines(); talking = false; if (ui) ui.EndModal(); }
    }
}

