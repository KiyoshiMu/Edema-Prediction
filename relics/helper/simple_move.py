import os, shutil, sys

def main(ref: str, beg: str, dst: str) -> None:
    refs = os.listdir(ref)
    for d in refs:
        start_dir = os.path.join(beg, d)
        end_dir = os.path.join(dst, d)
        shutil.move(start_dir,end_dir)

if __name__ == "__main__":
    ref = sys.argv[1]
    beg = sys.argv[2]
    dst = sys.argv[3]
    main(ref, beg, dst)