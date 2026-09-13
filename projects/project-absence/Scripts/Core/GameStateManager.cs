using UnityEngine;

public enum GameDay
{
    Day0,
    Day1,
    Day2,
    Day3
}

/// <summary>
/// 날짜, 자각도 점수, 엄마에게 저항했는지와 최종 엔딩을 관리합니다.
/// 자세한 수정 위치는 Documentation/01_코드와_수정안내.md를 참고하세요.
/// </summary>
[AddComponentMenu("결석/진행 상태와 엔딩 판정")]
public class GameStateManager : MonoBehaviour
{
    public static GameStateManager Instance { get; private set; }

    [Header("진행 상태")]
    [SerializeField] private GameDay currentDay = GameDay.Day0;
    [SerializeField] private int memoryScore;
    [SerializeField, Min(1)] private int awarenessThreshold = 6;
    [SerializeField] private bool dayZeroRoofFallOccurred;

    [Header("결과 판정")]
    [SerializeField] private bool hiddenDayZeroExit;
    [SerializeField] private bool motherResisted;
    [SerializeField] private bool qteActive;
    [SerializeField] private bool gameOver;

    public GameDay CurrentDay => currentDay;
    public int MemoryScore => memoryScore;
    public bool IsAware => memoryScore >= awarenessThreshold;
    public bool DayZeroRoofFallOccurred => dayZeroRoofFallOccurred;
    public bool HiddenDayZeroExit => hiddenDayZeroExit;
    public bool MotherResisted => motherResisted;
    public bool QteActive => qteActive;
    public bool IsGameOver => gameOver;

    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }

        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    public void SetDay(GameDay day)
    {
        currentDay = day;
    }

    public void AddMemory(int value)
    {
        memoryScore = Mathf.Max(0, memoryScore + value);
        Debug.Log($"MemoryScore: {memoryScore}");
    }

    public void SetHiddenDayZeroExit(bool value)
    {
        hiddenDayZeroExit = value;
    }

    public void SetMotherResisted(bool value)
    {
        motherResisted = value;
    }

    public void StartQTE()
    {
        qteActive = true;
    }

    public void FinishQTE()
    {
        qteActive = false;
    }

    public string ResolveEnding()
    {
        if (hiddenDayZeroExit)
        {
            return "Day0 히든 루트: 결과 미정";
        }

        if (!motherResisted)
        {
            return IsAware ? "E2 귀환" : "E1 기억상실 각성";
        }

        return IsAware ? "E4 깨어 있는 꿈" : "E3 평범한 하루";
    }

    public void RecordDayZeroRoofFall()
    {
        // 추락 이벤트와 엔딩 확정은 별개입니다. 결과가 정해질 때 연결합니다.
        dayZeroRoofFallOccurred = true;
    }

    public void EndGame()
    {
        if (hiddenDayZeroExit) return;
        gameOver = true;
        Debug.Log("Ending: " + ResolveEnding());
    }
}

