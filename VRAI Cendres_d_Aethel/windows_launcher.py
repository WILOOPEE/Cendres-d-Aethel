import os, sys, runpy

def resource(name):
    root = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, name)

def main():
    print("CENDRES D'AETHEL")
    print("1. Edition Ultra Hard")
    print("2. Edition Monde ouvert")
    choice = input("Choisis une edition (1-2) : ").strip()
    script = {"1": "cendres_d_aethel.py", "2": "cendres_d_aethel_monde_ouvert.py"}.get(choice)
    if not script:
        print("Choix invalide.")
        input("Entree pour fermer...")
        return
    path = resource(script)
    os.chdir(os.path.dirname(path))
    sys.argv = [path]
    runpy.run_path(path, run_name="__main__")

if __name__ == "__main__":
    main()
