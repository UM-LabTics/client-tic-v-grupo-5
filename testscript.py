import argparse


def edit_env(door_id):
    with open('results.txt', 'w') as file:
        file.write(f"hola:{door_id}")

def main(door_id):
    edit_env()
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Door id')
    parser.add_argument('door_id', type=str, help='The door id')
    args = parser.parse_args()
    main(args.door_id)