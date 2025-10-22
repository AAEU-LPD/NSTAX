Community and Contributions
===========================

Contribution Guidelines
-----------------------
- Fork → Create branch → Code → Pull request
- Follow existing architecture and doc conventions

FAQ
---
**Q:** Do I need to know Python in depth?  
**A:** No. Basic scripting is sufficient to write tests.

**Q:** What if my equipment is not supported?  
**A:** Add a driver in `equipment/` using a compatible interface.

Troubleshooting
---------------
+----------------------+----------------------------+-----------------------------+
| Issue                | Cause                      | Fix                         |
+======================+============================+=============================+
| Test not found       | Name mismatch              | Check test_config.yaml      |
| Equipment error      | Address incorrect          | Validate instrument config  |
| No logs generated    | Logging misconfigured      | Check YAML log settings     |
+----------------------+----------------------------+-----------------------------+

Contact and Maintainers
------------------------
- LPD Validation Team:  seg_systest.eu@alpsalpine.com
- Internal Repo: https://github.com/AAEU-LPD/NSTA
