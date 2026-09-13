using UnityEngine;

// TextMesh 글꼴 아틀라스를 깊이 테스트용 재질에 전달하여 벽 뒤의 글씨를 숨깁니다.
[ExecuteAlways]
[RequireComponent(typeof(TextMesh))]
/// <summary>
/// TextMesh 글꼴 아틀라스를 갱신하여 표지판 글자가 벽 뒤로 비치지 않도록 합니다.
/// 자세한 수정 위치는 Documentation/01_코드와_수정안내.md를 참고하세요.
/// </summary>
[AddComponentMenu("결석/벽에 붙은 글자")]
public class HospitalWorldLabel : MonoBehaviour
{
    private void OnEnable() { Font.textureRebuilt += FontChanged; Refresh(); }
    private void OnDisable() { Font.textureRebuilt -= FontChanged; }
    private void FontChanged(Font font) { if (GetComponent<TextMesh>().font == font) Refresh(); }
    private void Refresh()
    {
        var text = GetComponent<TextMesh>();
        if (!text.font) return;
        var properties = new MaterialPropertyBlock();
        properties.SetTexture("_MainTex", text.font.material.mainTexture);
        GetComponent<Renderer>().SetPropertyBlock(properties);
    }
}

