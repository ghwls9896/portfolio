using UnityEngine;

// Day0 구역 안의 탐색 상태입니다. 자각도/최종 엔딩은 기존 GameStateManager가 관리합니다.
/// <summary>
/// 보호자 대화, 점검 기록, 카드 획득과 시설관리 문 해제 여부를 보관합니다. 전역 자각도와는 별도입니다.
/// 자세한 수정 위치는 Documentation/01_코드와_수정안내.md를 참고하세요.
/// </summary>
[AddComponentMenu("결석/병원 탐색 조건")]
public class HospitalAreaProgress : MonoBehaviour
{
    public bool NurseSpoken { get; private set; }
    public bool VisitorSpoken { get; private set; }
    public bool MaintenanceNoteRead { get; private set; }
    public bool SpareCardFound { get; private set; }
    public bool ServiceAccessUnlocked { get; private set; }
    public bool CanUseServicePanel => VisitorSpoken && MaintenanceNoteRead && SpareCardFound;
    public void MeetNurse() { NurseSpoken = true; }
    public void MeetVisitor() { VisitorSpoken = true; }
    public void ReadMaintenanceNote() { MaintenanceNoteRead = true; }
    public void FindSpareCard() { SpareCardFound = true; }
    public void UnlockServiceAccess() { ServiceAccessUnlocked = true; }
}

