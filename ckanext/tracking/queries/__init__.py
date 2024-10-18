"""
Relevant queries to tracking data
"""
import csv


def download_query_results_as_csv(query_results, filename):
    """
    Download query results as CSV
    """
    f = open(filename, 'w')
    writer = csv.writer(f)
    # include headers
    writer.writerow(query_results[0].keys())
    writer.writerows(query_results)
    f.close()
