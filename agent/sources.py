GN = "https://news.google.com/rss/search?q={q}&hl=en&gl=SA&ceid=SA:en"

SOURCES = {
    # Direct RSS feeds
    "Saudi Gazette":      "https://saudigazette.com.sa/rssFeed/74",
    "Arab News":          GN.format(q="site:arabnews.com+tourism"),
    "Al Jazeera English": "https://www.aljazeera.com/xml/rss/all.xml",
    "Skift":              "https://skift.com/feed/",
    # Per-outlet feeds via Google News (outlet blocks or removed its own RSS)
    "Gulf News":          GN.format(q="site:gulfnews.com+saudi"),
    "The National":       GN.format(q="site:thenationalnews.com+saudi"),
    "Al Arabiya English": GN.format(q="site:english.alarabiya.net+saudi+tourism"),
    "Arabian Business":   GN.format(q="site:arabianbusiness.com+saudi"),
    "Zawya":              GN.format(q="site:zawya.com+saudi+tourism"),
    # Topic feeds (multi-outlet)
    "Topic: Saudi tourism": GN.format(q="saudi+tourism"),
    "Topic: visa & entry":  GN.format(q="saudi+visa+OR+saudi+entry+OR+saudi+aviation"),
    "Topic: giga-projects": GN.format(q="NEOM+OR+%22Red+Sea+Global%22+OR+Diriyah+OR+AlUla"),
}