using UnityEngine;

// 의료 모니터의 연출용 파형입니다. 실제 진단 수치를 계산하지 않습니다.
/// <summary>
/// 병상 모니터의 파형과 수치를 연출합니다.
/// 자세한 수정 위치는 Documentation/01_코드와_수정안내.md를 참고하세요.
/// </summary>
[AddComponentMenu("결석/병실 모니터 파형")]
public class HospitalMonitorPulse : MonoBehaviour
{
    public LineRenderer trace;
    public float period = 0.92f;
    public int pointCount = 100;
    private void Update()
    {
        if (!trace) return;
        trace.positionCount = pointCount;
        for (int i = 0; i < pointCount; i++)
        {
            float x = i / (float)(pointCount - 1);
            float phase = Mathf.Repeat(x * 2.5f - Time.time / period, 1);
            float y = 0.007f * Mathf.Sin(phase * 6.28f);
            if (phase > .38f && phase < .42f) y -= .018f;
            if (phase >= .42f && phase < .46f) y += .11f * Mathf.Sin((phase - .42f) / .04f * Mathf.PI);
            if (phase >= .46f && phase < .50f) y -= .036f * Mathf.Sin((phase - .46f) / .04f * Mathf.PI);
            trace.SetPosition(i, new Vector3(-.205f + x * .41f, y, -.016f));
        }
    }
}

