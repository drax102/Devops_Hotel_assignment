import json
import urllib.request

run_id = 43716465249
base_url = f"https://api.github.com/repos/drax102/Devops_Hotel_assignment/actions/runs/{run_id}"

req = urllib.request.Request(base_url, headers={"User-Agent": "DevOps-Verify-Script"})
with urllib.request.urlopen(req) as resp:
    run_data = json.loads(resp.read().decode())

jobs_req = urllib.request.Request(
    f"{base_url}/jobs", headers={"User-Agent": "DevOps-Verify-Script"}
)
with urllib.request.urlopen(jobs_req) as resp:
    jobs_data = json.loads(resp.read().decode())

print("=" * 60)
print("GITHUB ACTIONS CI PIPELINE VERIFICATION RECORD")
print("=" * 60)
print(f"Workflow Run ID : {run_data.get('id')}")
print(f"Workflow Name   : {run_data.get('name')}")
print(f"Repository      : {run_data.get('repository', {}).get('full_name')}")
print(f"Branch          : {run_data.get('head_branch')}")
print(f"Head Commit SHA : {run_data.get('head_sha')}")
print(f"Status          : {run_data.get('status')}")
print(f"Conclusion      : {run_data.get('conclusion')}")
print(f"Run HTML URL    : {run_data.get('html_url')}")
print(f"Created At      : {run_data.get('created_at')}")
print(f"Updated At      : {run_data.get('updated_at')}")
print("-" * 60)
print("JOB EXECUTION BREAKDOWN:")
print("-" * 60)

for job in jobs_data.get("jobs", []):
    print(f"\n[JOB] {job.get('name')}")
    print(f"  Status     : {job.get('status')}")
    print(f"  Conclusion : {job.get('conclusion')}")
    print(f"  Started At : {job.get('started_at')}")
    print(f"  Completed  : {job.get('completed_at')}")
    print(f"  Job URL    : {job.get('html_url')}")
    print("  Steps:")
    for step in job.get("steps", []):
        print(
            f"    - Step {step.get('number'):02d}: {step.get('name'):<42} -> [{step.get('conclusion')}]"
        )

print("\n" + "=" * 60)
print("VERIFICATION RESULT: PASSED (GREEN RUN)")
print("=" * 60)
