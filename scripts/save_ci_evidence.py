import json
import urllib.request

# Run IDs for verified runs: 43716465249 (feat/ci-pipeline), 43716727141 (main)
run_ids = [43716465249, 43716727141]

for run_id in run_ids:
    base_url = f"https://api.github.com/repos/drax102/Devops_Hotel_assignment/actions/runs/{run_id}"

    req = urllib.request.Request(
        base_url, headers={"User-Agent": "DevOps-Verify-Script"}
    )
    with urllib.request.urlopen(req) as resp:
        run_data = json.loads(resp.read().decode())

    jobs_req = urllib.request.Request(
        f"{base_url}/jobs", headers={"User-Agent": "DevOps-Verify-Script"}
    )
    with urllib.request.urlopen(jobs_req) as resp:
        jobs_data = json.loads(resp.read().decode())

    print(f"run_id: {run_data.get('id')}")
    print(f"name: {run_data.get('name')}")
    print(f"event: {run_data.get('event')}")
    print(f"head_branch: {run_data.get('head_branch')}")
    print(f"head_sha: {run_data.get('head_sha')}")
    print(f"status: {run_data.get('status')}")
    print(f"conclusion: {run_data.get('conclusion')}")
    print(f"html_url: {run_data.get('html_url')}")
    print(f"created_at: {run_data.get('created_at')}")
    print(f"updated_at: {run_data.get('updated_at')}")

    for job in jobs_data.get("jobs", []):
        print(f"job_id: {job.get('id')}")
        print(f"job_name: {job.get('name')}")
        print(f"job_status: {job.get('status')}")
        print(f"job_conclusion: {job.get('conclusion')}")
        print(f"job_html_url: {job.get('html_url')}")
        for step in job.get("steps", []):
            print(
                f"step_number: {step.get('number')} | step_name: {step.get('name')} | step_status: {step.get('status')} | step_conclusion: {step.get('conclusion')}"
            )
    print()
