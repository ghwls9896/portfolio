using System.Collections;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

// 병원 대화 표시만 담당합니다. 순서와 카메라 전환은 IntroSequence가 담당합니다.
/// <summary>
/// 한글 대사 출력, 조사 문구, 대화 중 이동 잠금과 해제를 담당합니다. 이야기 진행 조건은 다른 컴포넌트가 정합니다.
/// 자세한 수정 위치는 Documentation/01_코드와_수정안내.md를 참고하세요.
/// </summary>
[AddComponentMenu("결석/대화 창과 입력 잠금")]
public class HospitalDialogueUI : MonoBehaviour
{
    public CanvasGroup panel;
    public Text speakerText;
    public Text dialogueText;
    public Text continueText;
    public Text hintText;
    public Text chapterText;
    public Text observationText;
    [Min(1)] public float charactersPerSecond = 28f;
    private Coroutine observation;
    public bool IsBusy { get; private set; }
    private FirstPersonController lockedMovement;
    private PlayerInteraction lockedInteraction;
    private bool previousMovement, previousInteraction;
    private CursorLockMode previousCursor;
    private bool previousCursorVisible;

    // 복도 대화와 관리 패널이 동일한 입력 잠금을 사용합니다.
    public bool BeginModal(FirstPersonController movement, PlayerInteraction interaction)
    {
        if (IsBusy) return false;
        IsBusy = true;
        lockedMovement = movement; lockedInteraction = interaction;
        previousMovement = movement && movement.enabled;
        previousInteraction = interaction && interaction.enabled;
        previousCursor = Cursor.lockState; previousCursorVisible = Cursor.visible;
        if (movement) movement.enabled = false;
        if (interaction) interaction.enabled = false;
        if (observation != null) StopCoroutine(observation);
        observationText.text = ""; hintText.text = "";
        Cursor.lockState = CursorLockMode.None; Cursor.visible = false;
        return true;
    }

    public void EndModal()
    {
        if (!IsBusy) return;
        HideDialogue();
        if (lockedMovement) lockedMovement.enabled = previousMovement;
        if (lockedInteraction) lockedInteraction.enabled = previousInteraction;
        Cursor.lockState = previousCursor; Cursor.visible = previousCursorVisible;
        IsBusy = false;
    }

    public static bool AdvancePressed => Keyboard.current != null &&
        (Keyboard.current.spaceKey.wasPressedThisFrame || Keyboard.current.enterKey.wasPressedThisFrame);

    public IEnumerator Say(string speaker, string line)
    {
        panel.alpha = 1;
        speakerText.text = speaker;
        dialogueText.text = "";
        continueText.text = "SPACE  ·  문장 펼치기";
        float visible = 0;
        // 이전 문장을 넘긴 입력이 다음 문장까지 넘기지 않도록 한 프레임 기다립니다.
        yield return null;
        while (visible < line.Length)
        {
            if (AdvancePressed) break;
            visible += Time.unscaledDeltaTime * charactersPerSecond;
            dialogueText.text = line.Substring(0, Mathf.Min(line.Length, (int)visible));
            yield return null;
        }
        dialogueText.text = line;
        continueText.text = "SPACE  ·  계속";
        yield return null;
        while (!AdvancePressed) yield return null;
    }

    public void HideDialogue() { panel.alpha = 0; }

    public void ShowObservation(string text)
    {
        if (observation != null) StopCoroutine(observation);
        observation = StartCoroutine(Observe(text));
    }

    private IEnumerator Observe(string text)
    {
        observationText.text = text;
        yield return new WaitForSeconds(6f);
        observationText.text = "";
        observation = null;
    }
}

