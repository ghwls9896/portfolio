using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

/// <summary>
/// 탐색 조건 확인 후 숫자 입력 창을 열고 비밀번호가 맞으면 시설관리 출입을 허용합니다.
/// 자세한 수정 위치는 Documentation/01_코드와_수정안내.md를 참고하세요.
/// </summary>
[AddComponentMenu("결석/시설관리 비밀번호")]
public class HospitalServicePanel : MonoBehaviour, IInteractable
{
    public HospitalAreaProgress progress;
    public HospitalDialogueUI ui;
    public FirstPersonController movement;
    public PlayerInteraction interaction;
    public GameObject panel;
    public Text display;
    public string accessCode = "0417";
    public bool IsOpen { get; private set; }
    private string entered = "";
    public string InteractionText => "관리 패널을 살펴본다";
    public bool TryInteract()
    {
        if (progress.ServiceAccessUnlocked) { ui.ShowObservation("출입 승인이 유지되고 있다."); return true; }
        if (!progress.CanUseServicePanel) { ui.ShowObservation("승인 카드와 점검 기록이 필요하다. 어디서부터 찾아야 할까."); return false; }
        if (!ui.BeginModal(movement, interaction)) return false;
        entered = ""; IsOpen = true; panel.SetActive(true); UpdateDisplay(); return true;
    }
    private void Update()
    {
        if (!IsOpen || Keyboard.current == null) return;
        var k = Keyboard.current;
        if (k.escapeKey.wasPressedThisFrame) { Close(); return; }
        for (int i = 0; i < 10; i++)
        {
            Key top = i == 0 ? Key.Digit0 : (Key)((int)Key.Digit1 + i - 1);
            Key pad = (Key)((int)Key.Numpad0 + i);
            if (k[top].wasPressedThisFrame || k[pad].wasPressedThisFrame) AddDigit(i);
        }
        if (k.backspaceKey.wasPressedThisFrame && entered.Length > 0) { entered = entered.Substring(0, entered.Length - 1); UpdateDisplay(); }
        if (k.enterKey.wasPressedThisFrame || k.numpadEnterKey.wasPressedThisFrame) Submit();
    }
    public void AddDigit(int value)
    {
        if (!IsOpen || value < 0 || value > 9 || entered.Length == 4) return;
        entered += value.ToString(); UpdateDisplay();
    }
    public bool Submit()
    {
        if (!IsOpen) return false;
        if (entered != accessCode)
        { entered = ""; display.text = "기록과 일치하지 않습니다.\n\n_  _  _  _"; return false; }
        progress.UnlockServiceAccess(); Close(); ui.ShowObservation("작은 잠금 소리가 들렸다."); return true;
    }
    private void UpdateDisplay() { display.text = "시설 점검 시각\n\n" + string.Join("  ", entered.PadRight(4, '_').ToCharArray()); }
    public void Close()
    { if (!IsOpen) return; IsOpen = false; panel.SetActive(false); ui.EndModal(); }
    private void OnDisable() { if (IsOpen) Close(); }
}

