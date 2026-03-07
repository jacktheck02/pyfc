#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <chrono>
#include <ctime>
#include <iomanip>
#include <sstream>
#include <cstdlib>
#include <filesystem>
#include <fstream>
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

std::string get_today_date() {
    auto now = std::chrono::system_clock::now();
    std::time_t now_time_t = std::chrono::system_clock::to_time_t(now);
    std::tm* now_tm = std::localtime(&now_time_t);

    std::ostringstream oss;
    oss << std::put_time(now_tm, "%Y-%m-%d");
    return oss.str();
}

std::string get_tomorrow_date() {
    auto now = std::chrono::system_clock::now();
    auto tomorrow = now + std::chrono::hours(24);
    std::time_t tomorrow_time_t = std::chrono::system_clock::to_time_t(tomorrow);
    std::tm* tomorrow_tm = std::localtime(&tomorrow_time_t);

    std::ostringstream oss;
    oss << std::put_time(tomorrow_tm, "%Y-%m-%d");
    return oss.str();
}

void parse_and_display_matches(const json& response_json) {
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
        return;
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
}

int main(int argc, char* argv[]) {
    std::string cache_dir;
    if (!std::getenv("XDG_CACHE_HOME")) {
        if (!std::getenv("HOME")) {
            std::cerr << "Error: HOME environment variable is not set.\n";
            return 1;
        } else {
            cache_dir = std::string(std::getenv("HOME")) + "/.cache/clifc";
        }
    } else {
        cache_dir = std::string(std::getenv("XDG_CACHE_HOME")) + "/clifc";
    }

    std::ifstream cache_file(cache_dir + "/football_matches_cache.json");
    json cache_json;
    if (cache_file.is_open()) {
        try {
            cache_file >> cache_json;
        } catch (json::parse_error& e) {
            std::cerr << "Failed to parse cache JSON: " << e.what() << "\n";
        }
    }

    std::string today = get_today_date();
    std::string tomorrow = get_tomorrow_date();
    if (cache_json.contains("filters") && cache_json["filters"].contains("dateFrom") && cache_json["filters"].contains("dateTo") &&
        cache_json["filters"]["dateFrom"] == today && cache_json["filters"]["dateTo"] == tomorrow) {
        parse_and_display_matches(cache_json);
        return 0;
    } 

    const char* api_key_env = std::getenv("FOOTBALL_API_KEY");
    if (!api_key_env) {
        std::cerr << "Error: FOOTBALL_API_KEY environment variable is not set.\n";
        std::cerr << "Please set it using: export FOOTBALL_API_KEY='your_api_key_here'\n";
        return 1;
    }
    std::string api_key = api_key_env;

    std::string url = "https://api.football-data.org/v4/matches";
    
    cpr::Response r = cpr::Get(cpr::Url{url},
                            cpr::Header{{"X-Auth-Token", api_key}},
                            cpr::Parameters{{"dateFrom", today}, {"dateTo", tomorrow}});

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

    try {
        std::filesystem::create_directories(cache_dir);
        std::ofstream out_cache_file;
        out_cache_file.open(cache_dir + "/football_matches_cache.json");
        if (!out_cache_file.is_open()) {
            std::cerr << "Cache file not written.\n";
        } else {
            out_cache_file << response_json.dump(4);
            out_cache_file.close();
        }
    } catch (const std::filesystem::filesystem_error& e) {
        std::cerr << "Failed to create cache directory: " << e.what() << "\n";
    }
    
    parse_and_display_matches(response_json);
    return 0;
}
