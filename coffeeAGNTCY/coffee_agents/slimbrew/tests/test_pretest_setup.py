import subprocess

def setup_farms():
    """
    Pretest setup to start the empire farm, coruscant farm, naboo farm, and tatooine farm.
    """
    farms = [
        "empire.py",
        "coruscant-farm.py",
        "naboo-farm.py",
        "tatooine-farm.py"
    ]
    processes = []
    for farm in farms:
        process = subprocess.Popen(["python", farm])
        processes.append(process)
    return processes

def teardown_farms(processes):
    """
    Teardown the farms after tests.
    """
    for process in processes:
        process.terminate()

if __name__ == "__main__":
    processes = setup_farms()
    print("Farms are running. Press Ctrl+C to stop.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        teardown_farms(processes)