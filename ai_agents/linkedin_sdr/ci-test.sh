set -e
#pip3 install -r requirements.test.txt
# pytest test/test_dummy.py --disable-pytest-warnings
# python -m tests.coverage_output
mkdir -p artifacts
mkdir coverage
touch coverage/coverage_output.json
python3 dump_coverage.py
mv coverage/** /mnt/artifacts 