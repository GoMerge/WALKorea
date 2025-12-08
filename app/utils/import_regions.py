import csv
from app.database import SessionLocal
from app.models.region import Region
import os

def parse_level_and_parent(name):
    tokens = name.split()
    if len(tokens) == 1:
        level = 1
        parent_name = None
    elif len(tokens) == 2:
        level = 2
        parent_name = tokens[0]
    else:
        level = len(tokens)
        parent_name = " ".join(tokens[:-1])
    return level, parent_name

def import_region_tree(file_path):
    full_path = os.path.abspath(file_path)
    if not os.path.exists(full_path):
        print(f"파일을 찾을 수 없음: {full_path}")
        return
    with open(full_path, "r", encoding="cp949") as f:
        reader = csv.reader(f, delimiter=',')
        with SessionLocal() as session:
            name_to_id = {}
            row_count = 0
            for row in reader:
                if len(row) < 3:
                    print(f"잘못된 행 스킵됨: {row}")
                    continue
                code, name, status = row[0], row[1], row[2]
                if 'E' in code:
                    try:
                        code = str(int(float(code)))
                    except:
                        print(f"코드 변환 실패: {code}")
                        continue
                if status.strip() != "존재":
                    continue
                level, parent_name = parse_level_and_parent(name.strip())
                parent_id = name_to_id.get(parent_name) if parent_name else None
                tokens = name.strip().split()
                region = Region(
                    code=code,
                    name=tokens[-1] if tokens else "",
                    parent_id=parent_id,
                    level=level,
                    sido=tokens[0] if len(tokens) >= 1 else None,
                    gungu=tokens[1] if len(tokens) >= 2 else None,
                    myeon_eupdong=tokens[2] if len(tokens) >= 3 else None,
                    ri_dong=tokens[3] if len(tokens) >= 4 else None,
                    full_name=name.strip()
                )
                session.add(region)
                session.flush()  # PK 확보
                name_to_id[name.strip()] = region.id
                row_count += 1
            session.commit()
    print(f"계층 트리 지역 데이터 저장 완료. 저장 행수: {row_count}")

if __name__ == "__main__":
    # 데이터 파일 경로를 실제 파일 위치에 맞게 수정하세요
    import_region_tree("data/regions.csv")
