# -*- coding: utf-8 -*-
"""사무자동화산업기사 교재 지원 페이지 생성기(2026-11-12).

python tools/build_site.py
  1) 90_자산/실습파일/ 의 45개 파일을 files/ 아래로 복사하고 크기·SHA-256 앞 8자리를 계산한다.
  2) 2권 부록 a2_파일목록.md 의 확인값과 대조해 불일치를 출력한다(불일치가 있으면 종료 코드 1).
  3) 전체 묶음 zip 을 만들고, data/faq.json·errata.json·videos.json·config.json 으로 6개 쪽을 만든다.
  4) 표지 축소판과 QR 그림을 assets/ 에 둔다.
쪽 주소는 교재 QR 이 가리키므로 바꾸지 않는다: / · /files/ · /errata/ · /faq/ · /videos/ · /report/
"""
import hashlib
import html
import io
import json
import os
import re
import shutil
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET = os.path.dirname(SITE)                                   # 90_자산
ROOT = os.path.dirname(ASSET)                                   # 작업장
SRC_FILES = os.path.join(ASSET, "실습파일")
A2 = os.path.join(ROOT, "20_원고", "2권", "a2_파일목록.md")
sys.path.insert(0, os.path.join(ASSET, "그림", "appendix"))
from make_appendix import DESC, ORDER  # noqa: E402

CFG = json.load(io.open(os.path.join(SITE, "data", "config.json"), encoding="utf-8"))
BASE = CFG["base_url"].rstrip("/") + "/"
E = html.escape
NAV = [("", "홈"), ("files/", "실습 파일"), ("errata/", "정오표"), ("faq/", "자주 묻는 질문"), ("videos/", "영상"), ("report/", "오류 제보")]
FONT = '<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css" crossorigin>'


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def page(rel, title, body, desc):
    depth = rel.count("/")
    up = "../" * depth
    cur = rel
    nav = "".join(f'<a href="{up}{href}"{" aria-current=\"page\"" if href == cur else ""}>{E(name)}</a>' for href, name in NAV)
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
{FONT}
<link rel="stylesheet" href="{up}assets/site.css">
</head>
<body>
<header class="top"><div class="wrap">
<a class="brand" href="{up}">사무자동화산업기사 <span class="tag">교재 지원</span></a>
<nav class="nav" aria-label="교재 지원 메뉴">{nav}</nav>
</div></header>
{body}
<footer class="foot"><div class="wrap">
<img src="{up}assets/qr_home.png" alt="교재 지원 페이지 QR 코드">
<div><b>『2027 사무자동화산업기사』 교재 지원 페이지</b><br>이수미 지음 · 1권 필기 · 2권 실기<br>
주소 <span class="num">{E(BASE)}</span><br>
필기 CBT·실기 시뮬레이터의 문항과 과제는 모두 저자가 새로 작성했습니다. 시험 문항 복원 자료는 제공하지 않습니다.</div>
</div></footer>
</body>
</html>
"""


def band(chip, title, right=""):
    r = f"<p>{E(right)}</p>" if right else ""
    return f'<div class="band"><span class="chip">{E(chip)}</span><h1>{E(title)}</h1>{r}</div>'


def para(text):
    """faq 답 문자열: '- ' 로 시작하는 줄 묶음은 목록, 나머지는 문단."""
    lines = text.split("\n")
    if all(l.startswith("- ") for l in lines):
        return "<ul>" + "".join(f"<li>{E(l[2:])}</li>" for l in lines) + "</ul>"
    return "<p>" + E(text) + "</p>"


# ---------------------------------------------------------------- 실습 파일
def build_files():
    a2 = io.open(A2, encoding="utf-8").read()
    book = {m.group(1): m.group(2) for m in re.finditer(r"^\| [^|]+ \| (\S+) \| [^|]* \| \d+ \| ([0-9a-f]{8}) \|$", a2, flags=re.M)}
    out_dir = os.path.join(SITE, "files")
    rows, mismatch = [], []
    for d in ORDER:
        src = os.path.join(SRC_FILES, d)
        names = sorted(os.listdir(src), key=lambda n: (("시작" not in n) + ("완성" not in n) * 1 + ("견본" in n) * 2, n))
        os.makedirs(os.path.join(out_dir, d), exist_ok=True)
        for n in names:
            p = os.path.join(src, n)
            dst = os.path.join(out_dir, d, n)
            if not os.path.exists(dst) or sha(dst) != sha(p):
                shutil.copyfile(p, dst)
            h = sha(p)
            ch, desc = DESC.get(n, (d, ""))
            rows.append(dict(folder=d, name=n, ch=ch, desc=desc, kb=round(os.path.getsize(p) / 1024), sha8=h[:8], sha=h))
            if book.get(n) != h[:8]:
                mismatch.append((n, book.get(n), h[:8]))
    zname = CFG["zip_name"]
    zpath = os.path.join(out_dir, zname)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for r in rows:
            info = zipfile.ZipInfo(f"{r['folder']}/{r['name']}", date_time=(2026, 11, 12, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.flag_bits |= 0x800                                  # 파일 이름 UTF-8 표시
            with open(os.path.join(SRC_FILES, r["folder"], r["name"]), "rb") as f:
                z.writestr(info, f.read())
    zkb = round(os.path.getsize(zpath) / 1024)
    json.dump(dict(files=rows, zip=dict(name=zname, kb=zkb, sha8=sha(zpath)[:8])), io.open(os.path.join(SITE, "data", "files.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"실습 파일 {len(rows)}개, zip {zkb} KB, 부록 확인값 불일치 {len(mismatch)}")
    for m in mismatch:
        print("  불일치", m)
    return rows, zname, zkb, mismatch


def files_page(rows, zname, zkb):
    groups = {}
    for r in rows:
        groups.setdefault(r["ch"] if not r["ch"].startswith("세트") else "16장 " + r["ch"], []).append(r)
    trs = []
    for g, items in groups.items():
        trs.append(f'<tr class="grp"><td colspan="4">{E(g)}</td></tr>')
        for r in items:
            href = f"{r['folder']}/{r['name']}"
            trs.append(f'<tr><td><a class="dl" href="{E(href)}" download>{E(r["name"])}</a></td><td>{E(r["desc"])}</td>'
                       f'<td class="kb">{r["kb"]:,}</td><td class="hash">{r["sha8"]}</td></tr>')
    body = f"""<main><div class="wrap">
{band("FILES", "실습 파일", f"{len(rows)}개 · 2권 10~16장")}
<div class="page-intro">2권 실기 10~15장의 시작·완성 파일과 출력 견본, 16장 모의평가 4세트의 파일입니다. 장마다 시작 파일에서 따라 하기를 시작하고, 완성 파일과 출력 견본으로 결과를 대조합니다.</div>
<section class="sec">
<div class="sec-h"><span class="no">01</span><h2>한 번에 내려받기</h2></div>
<p><a class="btn" href="{E(zname)}" download>전체 묶음 내려받기 <span class="meta">ZIP · {zkb:,} KB · {len(rows)}개</span></a></p>
<div class="box"><span class="lab">열기 전</span><ul>
<li>바탕 화면에 연습용 폴더를 만들어 압축을 풉니다. 한글 파일 이름을 그대로 둡니다.</li>
<li>Excel·PowerPoint 파일이 보호된 보기로 열리면 편집 사용을 누릅니다. Access 파일은 보안 경고에서 콘텐츠 사용을 누릅니다.</li>
<li>출력 견본 PDF는 A4로 인쇄해 자기 출력물과 겹쳐 봅니다. 축소 인쇄하면 여백 비교가 어긋납니다.</li>
</ul></div>
</section>
<section class="sec">
<div class="sec-h"><span class="no">02</span><h2>파일 목록</h2><span class="sub">확인값 = SHA-256 앞 8자리</span></div>
<div class="tbl-wrap"><table>
<thead><tr><th>파일</th><th>내용</th><th>KB</th><th>확인값</th></tr></thead>
<tbody>{"".join(trs)}</tbody></table></div>
<div class="box key"><span class="lab">확인값 보는 법</span><p>Windows PowerShell에서 <code>Get-FileHash 파일명</code> 을 실행해 결과의 앞 8자리를 위 표와 비교합니다. 2권 부록의 시작·완성 파일 목록과 같은 값입니다.</p></div>
</section>
</div></main>"""
    return page("files/", "실습 파일 · 사무자동화산업기사 교재 지원", body, "2권 실기 시작·완성 파일, 출력 견본, 모의평가 4세트 파일 내려받기")


# ---------------------------------------------------------------- 정오표
def errata_page():
    data = json.load(io.open(os.path.join(SITE, "data", "errata.json"), encoding="utf-8"))
    secs = []
    for i, vol in enumerate(data["volumes"], 1):
        items = vol.get("items", [])
        if items:
            trs = "".join(f'<tr><td class="num">{E(it["page"])}</td><td>{E(it["where"])}</td><td>{E(it["wrong"])}</td><td>{E(it["right"])}</td><td class="num">{E(it["date"])}</td></tr>' for it in items)
            inner = f'<div class="tbl-wrap"><table><thead><tr><th>쪽</th><th>위치</th><th>잘못</th><th>바름</th><th>반영일</th></tr></thead><tbody>{trs}</tbody></table></div>'
        else:
            inner = '<div class="empty">등록된 정오 사항이 없습니다.</div>'
        secs.append(f'<section class="sec"><div class="sec-h"><span class="no">{i:02d}</span><h2>{E(vol["title"])}</h2><span class="sub">{E(vol["edition"])}</span></div>{inner}</section>')
    body = f"""<main><div class="wrap">
{band("ERRATA", "정오표", "기준일 " + data["updated"])}
<div class="page-intro">교재 본문, 필기 CBT, 실기 시뮬레이터에서 확인된 오류와 바른 내용을 판·쇄별로 적습니다. 오류를 발견하면 <a href="../report/">오류 제보</a>로 알려 주십시오. 반영된 제보는 이 표에 반영일과 함께 올립니다.</div>
{"".join(secs)}
</div></main>"""
    return page("errata/", "정오표 · 사무자동화산업기사 교재 지원", body, "1권 필기·2권 실기·웹앱 정오표")


# ---------------------------------------------------------------- FAQ
def faq_page():
    data = json.load(io.open(os.path.join(SITE, "data", "faq.json"), encoding="utf-8"))
    out, n = [], 0
    for ci, cat in enumerate(data["categories"], 1):
        qs = []
        for it in cat["items"]:
            n += 1
            ans = "".join(para(a) for a in it["a"])
            qs.append(f'<details class="q" id="q{n}"><summary><span class="qn">Q{n}</span><span>{E(it["q"])}</span></summary>'
                      f'<div class="a">{ans}<span class="ref">근거 {E(it["ref"])}</span></div></details>')
        out.append(f'<section class="sec faq-cat"><div class="sec-h"><span class="no">{ci:02d}</span><h2>{E(cat["title"])}</h2><span class="sub">{len(cat["items"])}문항</span></div>{"".join(qs)}</section>')
    body = f"""<main><div class="wrap">
{band("FAQ", "자주 묻는 질문", f"{n}문항")}
<div class="page-intro">시험 형식, 실기 출력, 작업 조건, 연습 환경, 실습 파일에 관한 질문입니다. 답의 근거가 된 교재 절 번호를 함께 적었습니다. 공단 공고와 시험장 안내가 바뀌면 그 내용을 따릅니다.</div>
{"".join(out)}
</div></main>"""
    print("FAQ", n, "문항")
    return page("faq/", "자주 묻는 질문 · 사무자동화산업기사 교재 지원", body, "사무자동화산업기사 시험 형식·실기 출력·실격 항목·연습 환경 FAQ"), n


# ---------------------------------------------------------------- 영상
def videos_page():
    data = json.load(io.open(os.path.join(SITE, "data", "videos.json"), encoding="utf-8"))
    items = data.get("items", [])
    if items:
        trs = "".join(f'<tr><td>{E(v["section"])}</td><td><a href="{E(v["url"])}">{E(v["title"])}</a></td><td class="num">{E(v["length"])}</td></tr>' for v in items)
        inner = f'<div class="tbl-wrap"><table><thead><tr><th>장·절</th><th>영상</th><th>길이</th></tr></thead><tbody>{trs}</tbody></table></div>'
    else:
        inner = '<div class="empty">공개된 영상이 아직 없습니다. 영상이 공개되면 장·절 번호와 함께 이 목록에 추가합니다.</div>'
    body = f"""<main><div class="wrap">
{band("VIDEO", "영상", "장·절 단위")}
<div class="page-intro">교재의 장·절 번호와 같은 제목으로 영상을 올립니다. 영상 한 편은 본문 한 절에 대응합니다.</div>
<section class="sec"><div class="sec-h"><span class="no">01</span><h2>영상 목록</h2></div>{inner}</section>
</div></main>"""
    return page("videos/", "영상 · 사무자동화산업기사 교재 지원", body, "교재 장·절별 영상 목록")


# ---------------------------------------------------------------- 오류 제보
def report_page():
    url = CFG["report_url"]
    body = f"""<main><div class="wrap">
{band("REPORT", "오류 제보", "교재 · 필기 CBT · 실기 시뮬레이터")}
<div class="page-intro">교재 본문, 실습 파일, 필기 CBT, 실기 시뮬레이터에서 오류를 발견하면 아래 양식으로 알려 주십시오. 확인한 뒤 <a href="../errata/">정오표</a>에 반영합니다.</div>
<section class="sec">
<div class="sec-h"><span class="no">01</span><h2>제보 양식</h2></div>
<p><a class="btn" href="{E(url)}" rel="noopener">오류 제보하기 <span class="meta">{E(CFG["report_label"])}</span></a></p>
<div class="box key"><span class="lab">적어 주실 것</span><ol>
<li>권(1권 필기·2권 실기) 또는 웹앱 이름(필기 CBT·실기 시뮬레이터)</li>
<li>쪽 번호와 위치(절 번호, 표·그림 번호, 문항 번호, 단계 번호)</li>
<li>잘못된 내용과 바른 내용, 확인한 근거(실행 결과, Office 버전 등)</li>
</ol></div>
<div class="box warn"><span class="lab">주의</span><ul>
<li>이름·연락처·수험번호 같은 개인정보는 적지 않습니다.</li>
<li>시험 문항의 원문·보기·데이터를 옮겨 적지 않습니다.</li>
<li>다른 출판사 교재의 쪽을 촬영해 올리지 않습니다.</li>
</ul></div>
</section>
</div></main>"""
    return page("report/", "오류 제보 · 사무자동화산업기사 교재 지원", body, "교재·필기 CBT·실기 시뮬레이터 오류 제보")


# ---------------------------------------------------------------- 홈
def home_page(n_files, n_faq, zkb):
    cbt, sim = CFG["cbt_url"], CFG["sim_url"]
    body = f"""<section class="hero"><div class="wrap">
<div>
<p class="eyebrow">Industrial Engineer Office Automation · 2027</p>
<h1>사무자동화산업기사</h1>
<span class="vol">교재 지원</span><br>
<span class="slogan"><span>1권 필기 · 2권 실기 · 출제기준 2026–2028</span></span>
<p class="lead">『2027 사무자동화산업기사』의 실습 파일, 정오표, 자주 묻는 질문, 영상, 오류 제보를 한곳에 모았습니다. 필기 CBT와 실기 시뮬레이터는 로그인 없이 무료로 씁니다.</p>
<div class="pills">
<a class="pill purple" href="{E(cbt)}"><span class="k">필기</span>필기 CBT<span class="r">320문항</span></a>
<a class="pill green" href="{E(sim)}"><span class="k">실기</span>실기 시뮬레이터<span class="r">Office 없이</span></a>
<a class="pill blue" href="files/"><span class="k">파일</span>실습 파일<span class="r">{n_files}개</span></a>
<a class="pill red" href="errata/"><span class="k">정오</span>정오표<span class="r">판·쇄별</span></a>
</div>
</div>
<div class="covers">
<img src="assets/cover_vol1.png" alt="2027 사무자동화산업기사 1권 필기 앞표지" width="420" height="588">
<img src="assets/cover_vol2.png" alt="2027 사무자동화산업기사 2권 실기 앞표지" width="420" height="588">
</div>
</div></section>
<main><div class="wrap">
<section class="sec">
<div class="sec-h"><span class="no">01</span><h2>바로 가기</h2></div>
<div class="cards">
<a class="card" href="files/"><span class="chip">FILES</span><h3>실습 파일 {n_files}개</h3><p>2권 10~16장 시작·완성 파일, 출력 견본, 모의평가 4세트. 전체 묶음 {zkb:,} KB.</p></a>
<a class="card" href="errata/"><span class="chip">ERRATA</span><h3>정오표</h3><p>교재 본문과 두 웹앱에서 확인된 오류와 바른 내용.</p></a>
<a class="card" href="faq/"><span class="chip">FAQ</span><h3>자주 묻는 질문 {n_faq}문항</h3><p>합격 기준, 실격 항목, 출력 5매 순서, 피벗 두 상태 인쇄, 시험장 Office 버전.</p></a>
<a class="card" href="{E(cbt)}"><span class="chip">CBT</span><h3>필기 CBT</h3><p>모의고사 3회와 2~8장 대표 문제, 문항별 해설과 근거 절 번호.</p></a>
<a class="card" href="{E(sim)}"><span class="chip">SIMULATOR</span><h3>실기 시뮬레이터</h3><p>Excel·Access·PowerPoint 시험 장면 연습과 출력물 5매 자동 채점.</p></a>
<a class="card" href="report/"><span class="chip">REPORT</span><h3>오류 제보</h3><p>쪽 번호와 위치, 바른 내용을 적어 알려 주십시오.</p></a>
</div>
</section>
<section class="sec">
<div class="sec-h"><span class="no">02</span><h2>이 페이지의 원칙</h2></div>
<div class="box warn"><span class="lab">제공하지 않는 것</span><p>시험 문항을 복원한 자료는 제공하지 않습니다. 교재와 두 웹앱의 문항·과제는 모두 저자가 새로 작성했습니다.</p></div>
<div class="box key"><span class="lab">주소</span><p>이 페이지의 주소 <span class="num">{E(BASE)}</span>는 교재에 인쇄되는 고정 주소입니다. 하위 쪽 주소(/files/, /errata/, /faq/, /videos/, /report/)도 바꾸지 않습니다.</p></div>
</section>
</div></main>"""
    return page("", "사무자동화산업기사 교재 지원", body, "2027 사무자동화산업기사 1권 필기·2권 실기 교재 지원: 실습 파일, 정오표, FAQ, 영상, 오류 제보, 필기 CBT, 실기 시뮬레이터")


def assets():
    from PIL import Image
    import qrcode
    a = os.path.join(SITE, "assets")
    os.makedirs(a, exist_ok=True)
    for vol, src in ((1, "사무자동화산업기사_1권필기_앞표지_preview.png"), (2, "사무자동화산업기사_2권실기_앞표지_preview.png")):
        im = Image.open(os.path.join(ASSET, "표지", src)).convert("RGB")
        im = im.resize((420, round(im.height * 420 / im.width)), Image.LANCZOS)
        im.save(os.path.join(a, f"cover_vol{vol}.png"), optimize=True)
    for name, box, border in (("qr_home.png", 6, 2), ("qr_print_300dpi.png", 20, 4)):
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=box, border=border)
        qr.add_data(BASE)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        target = a if name == "qr_home.png" else os.path.join(SITE, "qr")
        os.makedirs(target, exist_ok=True)
        img.save(os.path.join(target, name), dpi=(300, 300))
    print("표지 축소판·QR 생성:", BASE)


def main():
    assets()
    rows, zname, zkb, mismatch = build_files()
    pages = {"files/": files_page(rows, zname, zkb), "errata/": errata_page(), "videos/": videos_page(), "report/": report_page()}
    faq_html, n_faq = faq_page()
    pages["faq/"] = faq_html
    pages[""] = home_page(len(rows), n_faq, zkb)
    for rel, text in pages.items():
        d = os.path.join(SITE, rel)
        os.makedirs(d, exist_ok=True)
        io.open(os.path.join(d, "index.html"), "w", encoding="utf-8", newline="\n").write(text)
    print("쪽", len(pages), "개 생성")
    return 1 if mismatch else 0


if __name__ == "__main__":
    sys.exit(main())
