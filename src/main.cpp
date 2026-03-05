#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <chrono>
#include <ctime>
#include <iomanip>
#include <sstream>
#include <cstdlib>
#include <langinfo.h>
#include <cpr/cpr.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

std::string utc_to_local_time(const std::string& utc_time_str) {
    std::tm tm = {};
    std::istringstream ss(utc_time_str);
    ss >> std::get_time(&tm, "%Y-%m-%dT%H:%M:%SZ");

    if (ss.fail()) {
        return "Unknown Time";
    }

#if defined(_WIN32)
    time_t utc_time = _mkgmtime(&tm);
#else
    time_t utc_time = timegm(&tm);
#endif

    std::tm* local_tm = std::localtime(&utc_time);

    std::ostringstream out;

    setlocale(LC_TIME, "");
    std::string tfmt = nl_langinfo(T_FMT_AMPM);

    bool prefers12h =
        (tfmt.find("%I") != std::string::npos) || (tfmt.find("%l") != std::string::npos);

    if (prefers12h) {
        out << std::put_time(local_tm, "%I:%M %p");
    } else {
        out << std::put_time(local_tm, "%H:%M");
    }
    return out.str();
}

int main() {
    const char* api_key_env = std::getenv("FOOTBALL_API_KEY");
    if (!api_key_env) {
        std::cerr << "Error: FOOTBALL_API_KEY environment variable is not set.\n";
        std::cerr << "Please set it using: export FOOTBALL_API_KEY='your_api_key_here'\n";
        return 1;
    }
    std::string api_key = api_key_env;

    std::string url = "https://api.football-data.org/v4/matches";
    
    cpr::Response r = cpr::Get(cpr::Url{url},
                               cpr::Header{{"X-Auth-Token", api_key}}); // Fetch matches from top 5 leagues and champions league

    if (r.status_code != 200) {
        std::cerr << "Failed to fetch matches. HTTP Status Code: " << r.status_code << "\n";
        std::cerr << "Response: " << r.text << "\n";
        return 1;
    }

    json response_json;
    try {
        response_json = json::parse(r.text);
    } catch (json::parse_error& e) {
        std::cerr << "Failed to parse JSON response: " << e.what() << "\n";
        return 1;
    }

    std::map<std::string, std::vector<json>> leagues;
    std::map<std::string, std::string> league_areas;
    
    if (response_json.contains("matches") && response_json["matches"].is_array()) {
        for (const auto& match : response_json["matches"]) {
            std::string comp_name = match["competition"]["name"].get<std::string>();
            std::string area = match["area"]["name"].get<std::string>();
            league_areas[comp_name] = area;
            leagues[comp_name].push_back(match);
        }
    }

    if (leagues.empty()) {
        std::cout << "No matches today!\n";
        return 0;
    }

    std::cout << "\n⚽ Today's Matches ⚽\n";
    std::cout << "=================================\n\n";

    for (const auto& [league_name, matches] : leagues) {
        std::cout << "🏆 " << league_name << " [" << league_areas[league_name] << "]\n";
        std::cout << "-----------------------\n";
        for (const auto& match : matches) {
            std::string home_team = match["homeTeam"]["name"].get<std::string>();
            std::string away_team = match["awayTeam"]["name"].get<std::string>();
            std::string utc_date = match["utcDate"].get<std::string>();
            
            std::string local_time = utc_to_local_time(utc_date);
            
            std::cout << "[" << local_time << "] " << home_team << " vs " << away_team << "\n";
        }
        std::cout << "\n";
    }

    return 0;
}
