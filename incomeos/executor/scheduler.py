# incomeos/executor/scheduler.py Ð´Ð¾Ñ‚Ð¾Ñ€Ñ… job() Ñ„ÑƒÐ½ÐºÑ†Ð¸Ð¹Ð³ ÑˆÐ¸Ð½ÑÑ‡Ð»ÑÑ…
def job():
    print(f"ðŸ”„ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ÐÐ²Ñ‚Ð¾Ð½Ð¾Ð¼ Ñ…Ð°Ð¹Ð»Ñ‚ ÑÑ…ÑÐ»Ð»ÑÑ...")

    # 1. Ð›Ð¾ÐºÐ°Ð» Ð³Ò¯Ð¹Ñ†ÑÑ‚Ð³ÑÐ» ÑˆÐ°Ð»Ð³Ð°Ñ…
    from .orchestrator import run_opportunity
    run_opportunity("data/github_repos", force=False)

    # 2. Ð”ÑÐ»Ñ…Ð¸Ð¹Ð½ Ñ‚Ò¯Ð²ÑˆÐ½Ð¸Ð¹ Ð¸Ð½Ñ‚ÐµÑ€Ð½ÑÑ‚ Ñ…Ð°Ð¹Ð»Ñ‚ Ñ…Ð¸Ð¹Ñ…
    from incomeos.search.web_scout import search_opportunities
    new_opps = search_opportunities("data/github_repos", max_results=5)

    if new_opps:
        print(f"âœ… {len(new_opps)} ÑˆÐ¸Ð½Ñ Ð±Ð¾Ð»Ð¾Ð¼Ð¶ Ð¾Ð»Ð´Ð»Ð¾Ð¾. incomeos.db-Ð´ Ñ…Ð°Ð´Ð³Ð°Ð»Ð°Ð³Ð´Ð»Ð°Ð°.")
    else:
        print("â„¹ï¸ Ð¨Ð¸Ð½Ñ Ð±Ð¾Ð»Ð¾Ð¼Ð¶ Ð¾Ð»Ð´ÑÐ¾Ð½Ð³Ò¯Ð¹, ÑÑÐ²ÑÐ» Ñ…Ð°Ð¹Ð»Ñ‚ Ð°Ð¼Ð¶Ð¸Ð»Ñ‚Ð³Ò¯Ð¹ Ð±Ð¾Ð»Ð»Ð¾Ð¾.")
