User Guide
==========

Installation Instructions
-------------------------
1. Install Python 3.8 or higher from `python.org <https://www.python.org/downloads/>`_.

2. Clone the repository

  ::

      git clone https://github.com/AAEU-LPD/NSTA

  
  .. NOTE::
     You need to be part of the github's AAEU-LPD organization to access the repository.

  The cloned folder structure should look like this:

  ::

    NSTA/
    ├── config/
    ├── devices/
    ├── equipment/
    ├── interface/
    ├── logger/
    ├── QMetry/
    ├── reports/
    ├── testscripts/
    ├── standalone_scripts/
    ├── docs/
    ├── static/
    ├── requirements.txt
    ├── build_doc.bat
    └── run.py

3. Install required Python packages

  ::

     pip install -r NSTA/requirements.txt

4. Set PYTHONPATH environment variable to include NSTA root folder. Example for Windows Command Prompt

  ::

     set PYTHONPATH=%PYTHONPATH%;C:\path\to\NSTA


Setting Up a Test Environment (Quick Dry Run Example)
---------------------------------------------------------
1. Connect all required DUTs and equipment.
   For a dry run nothing needs to be connected.

2. Configure test environment using `config/teststation_config.yaml`.

Example (dry) teststation_config.yaml
  ::

    device:
    - type: DummyDevice
      name: DUT_01

    equipment:
    - type: DummyEquipment
      name: EQUIP_01
      parameters:
        port: DummyPort1

3. Configure test suite using `config/test_config.yaml`.

Example (dry) test_config.yaml
  ::

    testsuite:
      -
        name: dummy_testscript
        tests:
        - name: DummyTestScript
          dut_index: 0

4. Run tests using 'run.py'

  ::
  
    python run.py

5. Test reports and logs are generated in the `reports/` folder. Each run creates a timestamped subfolder. Inside the subfolder:

 - Reports are stored as HTML as report.html
 - Logs are written as text as runlog.txt


