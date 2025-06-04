from collections import defaultdict
import config

def run(data_file=config.general.datafile, output_file=config.general.csvfile, ext_file=config.general.extfile, debug=False):
    # raise ValueError
    siz = 1 << 15
    cnt = 0
    id_map = {}
    name = []
    m = defaultdict(lambda: defaultdict(int))

    # 打开输入输出文件
    with open(data_file, "r") as fin, open(output_file, "w") as fout, open(ext_file, "w") as fext:

        # 读前两行写入 ext.txt
        for _ in range(config.anal.extlines):
            line = fin.readline()
            fext.write(line)
            if debug:
                print(f"[DEBUG] ext line: {line.strip()}")

        while True:
            x = fin.readline()
            if not x or x == "\n":
                break
            y = fin.readline()
            z = fin.readline()
            if not y or not z:
                break

            a = x.strip()
            b = y.strip()
            try:
                c = int(z.strip())
            except ValueError:
                if debug:
                    print(f"[WARNING] invalid int in line: {z.strip()}")
                continue

            if a not in id_map:
                cnt += 1
                id_map[a] = cnt
                name.append(a)
                if debug:
                    print(f"[DEBUG] New id_map entry: {a} -> {cnt}")

            prev_val = m[b][id_map[a]]
            m[b][id_map[a]] = max(prev_val, c)
            if debug:
                print(f"[DEBUG] m[{b}][{id_map[a]}] = {m[b][id_map[a]]} (was {prev_val})")

        # 输出 header
        fout.write("#, " + ", ".join(name) + "\n")
        if debug:
            print("[DEBUG] Header: " + ", ".join(name))

        # 输出每行数据
        for s, p in m.items():
            row = [s] + [str(p.get(i, 0)) for i in range(1, cnt + 1)]
            fout.write(", ".join(row) + "\n")
            if debug:
                print(f"[DEBUG] Row for {s}: {row}")
