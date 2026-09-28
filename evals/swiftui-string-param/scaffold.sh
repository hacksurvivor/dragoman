#!/usr/bin/env bash
# Seeds the workspace. Runs only with `claude plugin eval --scaffold`.
set -euo pipefail
mkdir -p MyApp
cat > MyApp/HomeView.swift <<'FIXTURE'
import SwiftUI

struct HomeView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                sectionHeader("Coming Up", icon: "calendar")
                sectionHeader("Your Week", icon: "chart.bar")
                Text("Recent activity")
            }
        }
    }

    private func sectionHeader(_ title: String, icon: String) -> some View {
        HStack {
            Image(systemName: icon)
            Text(title)
                .font(.headline)
        }
    }
}
FIXTURE
mkdir -p MyApp
cat > MyApp/Localizable.xcstrings <<'FIXTURE'
{
  "sourceLanguage" : "en",
  "strings" : {
    "Coming Up" : {
      "localizations" : {
        "ru" : {
          "stringUnit" : {
            "state" : "translated",
            "value" : "Ближайшие"
          }
        }
      }
    },
    "Recent activity" : {
      "localizations" : {
        "ru" : {
          "stringUnit" : {
            "state" : "translated",
            "value" : "Недавняя активность"
          }
        }
      }
    },
    "Your Week" : {
      "localizations" : {
        "ru" : {
          "stringUnit" : {
            "state" : "translated",
            "value" : "Ваша неделя"
          }
        }
      }
    }
  },
  "version" : "1.0"
}
FIXTURE
