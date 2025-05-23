from datetime import datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict

from utils.supabase_methods import get_work_experience


class JobRanker:
    def __init__(self, weights, max_experience_years=15):
        """
        Initialize the JobRanker with weights and the max experience threshold.

        Args:
            weights (dict): Weights for work_period, recency, and job_type.
            max_experience_years (int): Maximum years of experience to consider.
        """
        self.weights = weights
        self.max_experience_years = max_experience_years

    def _rank_jobs(self, jobs):
        """
        Rank jobs based on scores calculated using the algorithm.

        Args:
            jobs (list): List of job records.

        Returns:
            list: Ranked list of jobs with scores in descending order.
        """
        # Step 1: Initialize an empty dictionary to aggregate experiences by job title
        merged_jobs = defaultdict(
            lambda: {
                "work_periods": [],
                "time_since_last_work": float("inf"),
                "job_type": "part-time",
            }
        )

        # Step 2: Filter jobs to include only experiences from the last max_experience_years
        current_date = datetime.now()
        cutoff_date = current_date - relativedelta(years=self.max_experience_years)

        filtered_jobs = [
            job
            for job in jobs
            if datetime.strptime(job["work_period"]["end"], "%Y-%m") > cutoff_date
        ]

        # Step 3: Merge jobs with the same title
        for job in filtered_jobs:
            title = job["title"]
            work_period = job["work_period"]
            time_since_last_work = job["time_since_last_work"]
            job_type = job["job_type"]

            # Update merged_jobs
            merged = merged_jobs[title]
            merged["work_periods"].append(work_period)
            merged["time_since_last_work"] = min(
                merged["time_since_last_work"], time_since_last_work
            )
            if job_type == "full-time":
                merged["job_type"] = "full-time"

        # Merge work periods for each title
        for title, data in merged_jobs.items():
            periods = sorted(
                data["work_periods"],
                key=lambda x: datetime.strptime(x["start"], "%Y-%m"),
            )
            merged_periods = []
            current_start = None
            current_end = None

            for period in periods:
                start = datetime.strptime(period["start"], "%Y-%m")
                end = datetime.strptime(period["end"], "%Y-%m")

                if current_start is None:
                    current_start = start
                    current_end = end
                elif start <= current_end + relativedelta(
                    months=1
                ):  # Overlapping or contiguous
                    current_end = max(current_end, end)
                else:
                    # Append the merged period as strings
                    merged_periods.append(
                        {
                            "start": current_start.strftime("%Y-%m"),
                            "end": current_end.strftime("%Y-%m"),
                        }
                    )
                    current_start = start
                    current_end = end

            if current_start and current_end:
                # Append the last merged period as strings
                merged_periods.append(
                    {
                        "start": current_start.strftime("%Y-%m"),
                        "end": current_end.strftime("%Y-%m"),
                    }
                )

            merged_jobs[title]["work_periods"] = merged_periods

        # Step 4: Compute normalization factors
        max_duration = 0
        max_recency = 0

        for data in merged_jobs.values():
            durations = [
                (
                    datetime.strptime(period["end"], "%Y-%m")
                    - datetime.strptime(period["start"], "%Y-%m")
                ).days
                for period in data["work_periods"]
            ]
            max_duration = max(max_duration, sum(durations))
            max_recency = max(max_recency, data["time_since_last_work"])

        # Step 5: Initialize scores
        scores = []

        for title, data in merged_jobs.items():
            # Calculate duration in months
            total_duration = (
                sum(
                    (
                        datetime.strptime(period["end"], "%Y-%m")
                        - datetime.strptime(period["start"], "%Y-%m")
                    ).days
                    for period in data["work_periods"]
                )
                / 30.0
            )
            normalized_duration = (
                total_duration / max_duration if max_duration > 0 else 0
            )

            # Normalize recency
            normalized_recency = (
                (max_recency - data["time_since_last_work"]) / max_recency
                if max_recency > 0
                else 0
            )

            # Job type score
            job_type_score = 1.0 if data["job_type"] == "full-time" else 0.5

            # Calculate total score
            score = (
                self.weights["work_period"] * normalized_duration
                + self.weights["recency"] * normalized_recency
                + self.weights["job_type"] * job_type_score
            )
            scores.append((title, score))

        # Step 7: Sort scores by score in descending order
        ranked_jobs = sorted(scores, key=lambda x: x[1], reverse=True)

        # Step 8: Return the sorted list of scores
        return ranked_jobs

    def _convert_job_list(self, jobs):
        """
        Convert job list from original format to new format and calculate months since last work
        """
        today = datetime.now()

        def calculate_months_difference(end_date_str):
            if not end_date_str:
                return 0
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            diff = relativedelta(today, end_date)
            return diff.years * 12 + diff.months

        converted_jobs = []

        for job in jobs:
            # Handle end date for current work
            end_date = job["end_date"]
            if job["current_work"] and not end_date:
                end_date = today.strftime("%Y-%m-%d")

            # Convert dates to YYYY-MM format
            start_date = datetime.strptime(job["start_date"], "%Y-%m-%d").strftime(
                "%Y-%m"
            )
            end_date_formatted = (
                datetime.strptime(end_date, "%Y-%m-%d").strftime("%Y-%m")
                if end_date
                else None
            )

            # Calculate time since last work
            time_since_last_work = calculate_months_difference(end_date)

            # Create new job entry
            new_job = {
                "title": job["occupation"],
                "company": job["company_name"],
                "work_period": {"start": start_date, "end": end_date_formatted},
                "time_since_last_work": time_since_last_work,
                "job_type": "part-time" if job["part_time"] else "full-time",
            }

            converted_jobs.append(new_job)

        return converted_jobs

    def get_ranked_jobs(self):
        """
        Get the ranked jobs based on the current state of the JobRanker.

        Returns:
            list: Ranked list of jobs with scores in descending order.
        """
        jobs = get_work_experience()
        converted_jobs = self._convert_job_list(jobs)
        return self._rank_jobs(converted_jobs)
