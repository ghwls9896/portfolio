/// <summary>
/// E로 조사할 수 있는 대상의 공통 약속입니다.
/// 새 조사 대상을 만들 때 이 인터페이스를 구현하면 PlayerInteraction이 찾을 수 있습니다.
/// </summary>
public interface IInteractable
{
    /// <summary>바라볼 때 표시하는 문구. 더 이상 조사할 수 없으면 빈 문자열을 사용합니다.</summary>
    string InteractionText { get; }

    /// <summary>상호작용 조건을 확인하고 실행합니다. 실행되었으면 true를 반환합니다.</summary>
    bool TryInteract();
}
