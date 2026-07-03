#!/usr/bin/env python3
"""
一条命令出海报：读配置 → 注入模板 → 渲染成 PNG。
用法:
  python3 make_poster.py                       # 用 config.json → poster.png
  python3 make_poster.py config.json out.png   # 指定配置和输出
只改 config.json 里的文案/价格/讲师，就能出新海报，无需懂代码。
"""
import json, sys, os, subprocess
DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    cfg = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    out = sys.argv[2] if len(sys.argv) > 2 else "poster.png"
    if not os.path.isabs(cfg): cfg = os.path.join(DIR, cfg)
    if not os.path.isabs(out): out = os.path.join(os.getcwd(), out)
    data = open(cfg, encoding="utf-8").read()
    try:
        json.loads(data)
    except Exception as e:
        print("❌ config.json 格式错误（不是合法 JSON）：", e); sys.exit(1)
    tpl = open(os.path.join(DIR, "template.html"), encoding="utf-8").read()
    html = tpl.replace("__DATA__", data)
    tmp = os.path.join(DIR, "_render.html")
    open(tmp, "w", encoding="utf-8").write(html)
    subprocess.run([sys.executable, os.path.join(DIR, "render_poster.py"), tmp, out], check=True)
    print("✅ 海报已生成：", out)

if __name__ == "__main__":
    main()
