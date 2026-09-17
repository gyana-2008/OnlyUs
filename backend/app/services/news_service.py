import asyncio
import time
import xml.etree.ElementTree as ET
import httpx
from typing import List, Dict, Any, Optional

FALLBACK_ARTICLES: List[Dict[str, Any]] = [
    {
        "id": "art-world-01",
        "category": "world",
        "title": "Global Climate Accord Reaches Historic Milestone at Geneva Summit",
        "summary": "Delegates from 140 nations ratify unprecedented clean grid infrastructure pact aimed at accelerating zero-emission transition before 2035.",
        "content": """GENEVA — In what international observers are calling the most decisive multilateral environmental breakthrough in a decade, representatives from 140 nations concluded marathon negotiations in Geneva this morning by signing the Comprehensive Clean Grid Protocol.

The accord establishes binding commitments to triple cross-border clean transmission capacity by 2035 and provides a dedicated $450 billion green financing facility for developing nations.

"Today we moved past voluntary pledges into verifiable structural cooperation," declared Chief Rapporteur Elena Vance during the concluding plenary. "This protocol aligns transmission architecture across continents, ensuring renewable power generated in wind and solar corridors reaches metropolitan load centers seamlessly."

Market analysts expect private sector capital reallocation to commence immediately, with major multilateral banks already scheduling sovereign green bond issuances for the fourth quarter. The framework also introduces standardized digital emissions tracking, powered by distributed cryptographic ledgers to eliminate double-counting of carbon offset credits.""",
        "author": "Marcus Sterling",
        "source": "Global Wire",
        "image_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80",
        "published_at": "2025-05-20T08:30:00Z",
        "read_time": "4 min read",
        "is_trending": True,
        "is_breaking": True,
    },
    {
        "id": "art-tech-01",
        "category": "technology",
        "title": "Photonic Supercomputing Chip Exceeds Traditional Exascale Efficiency Thresholds",
        "summary": "Engineers demonstrate light-speed matrix computation with 90% reduction in thermal dissipation, opening new pathways for edge AI inference.",
        "content": """SAN FRANCISCO — Silicon Valley researchers unveiled an optical computing architecture today that replaces copper interconnects with integrated optical wave-guides, performing tensor multiplications at the speed of light.

The breakthrough, published in Advanced Physics Review, demonstrates continuous matrix calculations with less than one-tenth the thermal output of current state-of-the-art silicon accelerators.

"We have reached the physical boundaries of electron mobility and thermal bottlenecks in classical silicon," explained lead architect Dr. Hiroshi Tanaka. "By guiding multi-wavelength laser beams through nanometer-scale silicon resonators, our processor computes complex multi-dimensional vectors passively as light waves interfere with one another."

The implications for data centers are profound. Cooling infrastructure, which currently accounts for nearly 40 percent of total hyperscale power consumption, could be drastically downscaled. Commercial sampling of the first commercial co-packaged optical modules is scheduled for late 2025.""",
        "author": "Dr. Sarah Chen",
        "source": "Tech Horizon",
        "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",
        "published_at": "2025-05-20T07:15:00Z",
        "read_time": "5 min read",
        "is_trending": True,
        "is_breaking": False,
    },
    {
        "id": "art-india-01",
        "category": "india",
        "title": "National Semiconductor Mission Surpasses Annual Production Milestones in Dholera",
        "summary": "India's burgeoning high-tech manufacturing hub rolls out first batch of domestically packaged compound semiconductors for global automotive suppliers.",
        "content": """NEW DELHI & DHOLERA — India's ambitious drive toward semiconductor sovereignty reached a watershed moment this week as the first commercial shipment of domestically fabricated compound silicon chips rolled off the automated cleanroom lines in Gujarat's Dholera Special Investment Region.

The chips, engineered specifically for electric vehicle power management and high-frequency 5G telecommunications, passed rigorous tier-1 automotive certification on their initial trial runs.

"This is not merely about domestic assembly; this represents end-to-end precision fabrication on Indian soil," stated the Union Minister for Electronics and IT during an inaugural briefing. "Our ecosystem has grown from design houses to comprehensive foundry and advanced packaging capabilities in under four years."

Over 25 ancillary suppliers, spanning ultra-pure industrial chemical providers and specialty gas producers, have established manufacturing bases in the surrounding semiconductor cluster, generating an estimated 42,000 specialized engineering positions.""",
        "author": "Aarav Sharma",
        "source": "Deccan Chronicle Bureau",
        "image_url": "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=1200&q=80",
        "published_at": "2025-05-20T06:45:00Z",
        "read_time": "4 min read",
        "is_trending": True,
        "is_breaking": False,
    },
    {
        "id": "art-science-01",
        "category": "science",
        "title": "Deep Ocean Expedition Uncovers Uncatalogued Chemo-Synthetic Ecosystems in Marianas",
        "summary": "Submersible robotic probes reveal thriving bioluminescent organisms sustaining life completely independent of solar radiation.",
        "content": """HONOLULU — Operating at depths exceeding 9,000 meters beneath the Western Pacific, an international oceanographic consortium has documented what researchers are calling an entirely uncatalogued biological frontier.

Using deep-submergence autonomous vehicles outfitted with sapphire-glass imaging sensors and gentle hydraulic suction samplers, scientists recorded over forty distinct species of hydrothermal organisms thriving adjacent to serpentine mud volcanoes.

"The biochemistry here defies our standard paradigms of planetary habitability," noted principal investigator Dr. Corinne Leveque. "These organisms utilize iron-methane redox gradients rather than sunlight-driven photosynthesis. Their existence dramatically expands the parameters of where we might look for metabolic life on the ice-covered moons of Jupiter and Saturn."

Specimens gathered during the 40-day dive sequence will now undergo genomic sequencing at maritime laboratories in Woods Hole and Brest.""",
        "author": "Julian Thorne",
        "source": "Scientific Review",
        "image_url": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=1200&q=80",
        "published_at": "2025-05-19T21:20:00Z",
        "read_time": "6 min read",
        "is_trending": False,
        "is_breaking": False,
    },
    {
        "id": "art-business-01",
        "category": "business",
        "title": "Central Banks Signal Shift Toward Dynamic Liquidity Ratios Amid Algorithmic Trade Boom",
        "summary": "Financial regulators propose new real-time reserve requirements to stabilize automated trading corridors across Tokyo, London, and New York.",
        "content": """LONDON & NEW YORK — Following a closed-door symposium at the Bank for International Settlements, major central banks have published consultative guidelines recommending algorithmic liquidity buffers for institutional clearinghouses.

The proposed regulations require market makers deploying autonomous microsecond routing engines to maintain adaptive margin requirements based on predictive volatility indices rather than retrospective end-of-day calculations.

"Algorithmic execution speeds have outpaced statutory settlement windows," remarked Senior Economic Strategist Clara Montgomery. "By introducing machine-verifiable intraday capital adjustments, we provide a stabilizing shock-absorber that protects retail investors from cascading flash adjustments."

Equities markets responded with measured stability, with sovereign bond yields tightening across five-year tenors as institutional investors welcomed the regulatory certainty.""",
        "author": "Oliver Kingsley",
        "source": "Financial Chronicle",
        "image_url": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80",
        "published_at": "2025-05-20T05:10:00Z",
        "read_time": "5 min read",
        "is_trending": True,
        "is_breaking": False,
    },
    {
        "id": "art-sports-01",
        "category": "sports",
        "title": "Precision Biometrics Redefine Modern High-Altitude Endurance Training",
        "summary": "How elite marathon runners and mountaineers are combining metabolic continuous monitoring with altitude simulation to shatter athletic limits.",
        "content": """ST. MORITZ — In the snow-fringed training facilities of the Swiss Alps, Olympic endurance athletes are pioneering training regimens that look closer to aerospace telemetry than traditional track-and-field drills.

Continuous interstitial lactate sensors, non-invasive near-infrared muscle oximetry, and adaptive atmospheric sleep pods now allow physiologists to calibrate workouts with microscopic precision.

"We no longer guess whether an athlete is entering overtraining or under-recovery," explained high-performance coach Liam O'Connor. "We can evaluate cellular ATP regeneration in real time, adjusting cadence and nutritional timing before structural fatigue manifests."

The results are speaking for themselves. Over the past six months, three longstanding middle-distance continental records have been broken by athletes utilizing the protocol, sparking vigorous debate within athletic federations regarding technological training standards.""",
        "author": "Kieran Vance",
        "source": "Athletic Digest",
        "image_url": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?auto=format&fit=crop&w=1200&q=80",
        "published_at": "2025-05-19T18:40:00Z",
        "read_time": "4 min read",
        "is_trending": False,
        "is_breaking": False,
    },
    {
        "id": "art-lifestyle-01",
        "category": "lifestyle",
        "title": "The Renaissance of Tactile Living: Why Digital Natives Are Embracing Analog Craft",
        "summary": "From bespoke mechanical keyboards to darkroom film photography and fountain pens, physical craftsmanship finds a passionate modern following.",
        "content": """COPENHAGEN — In a sunlit studio in the Norrebro district of Copenhagen, twenty-something artisans gather weekly not to code or scroll, but to hand-bind parchment journals, develop 120-format medium film, and mill brass fountain pen nibs.

The phenomenon, termed by cultural sociologists as 'Tactile Intentionality', represents a deliberate counterweight to ubiquitous algorithmic feeds and frictionless digital conveniences.

"When everything in your professional life is ephemeral pixels that vanish on command, working with grain, ink, and wood anchors your sense of agency," reflects studio curator Freja Lind. "A handwritten letter or a photograph developed in chemical baths demands your absolute presence."

Retail data supports the cultural shift: boutique paper makers, manual typewriter restorers, and vinyl pressing plants are reporting record order backlogs, driven predominantly by customers under the age of thirty.""",
        "author": "Astrid Møller",
        "source": "Nordic Living",
        "image_url": "https://images.unsplash.com/photo-1507842229451-79b1be886a27?auto=format&fit=crop&w=1200&q=80",
        "published_at": "2025-05-20T04:20:00Z",
        "read_time": "4 min read",
        "is_trending": True,
        "is_breaking": False,
    },
    {
        "id": "art-trending-01",
        "category": "trending",
        "title": "Urban Rewilding Projects Transform European Metropolises Into Verdant Corridors",
        "summary": "Cities replace asphalt parking complexes with micro-forests and natural drainage riverbeds to combat heat islands and restore biodiversity.",
        "content": """PARIS — Across major urban centers from Paris to Milan and Vienna, civil engineers and landscape architects are systematically dismantling redundant concrete roadways and replacing them with self-sustaining native forest pockets.

The initiatives, known collectively as the 'Emerald Vein' movement, have already lowered central district summer surface temperatures by an average of 3.4 degrees Celsius while reducing stormwater runoff overflows by half.

"We spent the twentieth century treating natural elements as an adversary to be paved over," remarks urban planner Jean-Marc Dupont. "Today we recognize that biodiversity corridors are the most cost-effective municipal infrastructure available for climate resilience."

Songbirds and pollinator species that had vanished from European city centers for over five decades are now reproducing along rooftop meadows and former railway embankments.""",
        "author": "Camille Laurent",
        "source": "Urban Echo",
        "image_url": "https://images.unsplash.com/photo-1477959858617-67f30bc75b82?auto=format&fit=crop&w=1200&q=80",
        "published_at": "2025-05-20T09:00:00Z",
        "read_time": "3 min read",
        "is_trending": True,
        "is_breaking": False,
    }
]

# Additional articles across categories for deep reading
ADDITIONAL_ARTICLES = [
    {
        "id": "art-world-02",
        "category": "world",
        "title": "Nordic Clean Energy Grid Transmits Surplus Hydroelectric Power Across Baltic",
        "summary": "High-voltage undersea direct current interconnector brings record renewable energy share to continental Europe.",
        "content": "STOCKHOLM — A massive cross-border undersea transmission line spanning 480 kilometers beneath the Baltic Sea commenced full commercial operation yesterday...",
        "author": "Henrik Lindqvist",
        "source": "Baltic Standard",
        "image_url": "https://images.unsplash.com/photo-1466611653911-95081537e5b7?auto=format&fit=crop&w=800&q=80",
        "published_at": "2025-05-19T14:30:00Z",
        "read_time": "3 min read",
        "is_trending": False,
        "is_breaking": False,
    },
    {
        "id": "art-tech-02",
        "category": "technology",
        "title": "Open Source Foundation Releases Sovereign Small Language Models for Private Devices",
        "summary": "High-accuracy localized reasoning models operate entirely on consumer smartphone silicon without transmitting user tokens.",
        "content": "BERLIN — The Open Artificial Intelligence Consortium announced the public release of its 'MicroThought-7B' weight suite today...",
        "author": "Dr. Sarah Chen",
        "source": "Compute Weekly",
        "image_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=800&q=80",
        "published_at": "2025-05-19T16:45:00Z",
        "read_time": "4 min read",
        "is_trending": True,
        "is_breaking": False,
    },
    {
        "id": "art-india-02",
        "category": "india",
        "title": "UPI Crosses 18 Billion Monthly Transactions as Bilateral Linkages Expand Globally",
        "summary": "India's Unified Payments Interface sets new global benchmark with instant merchant remittances across Southeast Asia and Gulf corridors.",
        "content": "MUMBAI — Digital payments architecture spearheaded by the National Payments Corporation of India (NPCI) registered an unprecedented 18.4 billion transactions...",
        "author": "Priya Nambiar",
        "source": "Mint Financial",
        "image_url": "https://images.unsplash.com/photo-1563986768609-322da13575f3?auto=format&fit=crop&w=800&q=80",
        "published_at": "2025-05-19T12:10:00Z",
        "read_time": "3 min read",
        "is_trending": True,
        "is_breaking": False,
    },
    {
        "id": "art-business-02",
        "category": "business",
        "title": "Global Shipping Giants Accelerate Green Methanol Retrofits for Container Fleets",
        "summary": "Decarbonization mandates push maritime transport companies into largest dual-fuel propulsion upgrade in commercial history.",
        "content": "ROTTERDAM — At Europe's busiest maritime harbor, three 20,000-TEU container vessels completed shipyard conversions to dual-fuel green methanol systems this morning...",
        "author": "Oliver Kingsley",
        "source": "Maritime Commerce",
        "image_url": "https://images.unsplash.com/photo-1559136555-9303baea8ebd?auto=format&fit=crop&w=800&q=80",
        "published_at": "2025-05-18T19:00:00Z",
        "read_time": "4 min read",
        "is_trending": False,
        "is_breaking": False,
    }
]

ALL_ARTICLES = FALLBACK_ARTICLES + ADDITIONAL_ARTICLES

RSS_FEEDS = [
    {"category": "world", "url": "https://feeds.bbci.co.uk/news/world/rss.xml", "source": "BBC News"},
    {"category": "technology", "url": "https://techcrunch.com/feed/", "source": "TechCrunch"},
    {"category": "science", "url": "https://www.sciencedaily.com/rss/top/science.xml", "source": "ScienceDaily"},
]

class NewsService:
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: float = 0
        self._cache_ttl_seconds: int = 900 # 15 mins

    async def fetch_rss_feed(self, client: httpx.AsyncClient, feed_info: dict) -> List[Dict[str, Any]]:
        """Fetch and parse an RSS feed with graceful error handling."""
        items = []
        try:
            resp = await client.get(feed_info["url"], timeout=4.0)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                channel = root.find("channel")
                if channel is not None:
                    count = 0
                    for item in channel.findall("item"):
                        title = item.findtext("title")
                        desc = item.findtext("description") or ""
                        link = item.findtext("link") or ""
                        pub_date = item.findtext("pubDate") or ""
                        
                        if title:
                            # Clean HTML tags if any in description
                            clean_desc = desc.replace("<p>", "").replace("</p>", "").strip()[:240]
                            items.append({
                                "id": f"rss-{feed_info['category']}-{hash(title) % 1000000}",
                                "category": feed_info["category"],
                                "title": title.strip(),
                                "summary": clean_desc or title.strip(),
                                "content": f"{clean_desc}\n\nRead the complete reporting at: {link}",
                                "author": feed_info["source"],
                                "source": feed_info["source"],
                                "image_url": "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?auto=format&fit=crop&w=800&q=80",
                                "published_at": pub_date or "Recently",
                                "read_time": "3 min read",
                                "is_trending": False,
                                "is_breaking": False,
                                "external_url": link
                            })
                            count += 1
                            if count >= 6:
                                break
        except Exception:
            pass
        return items

    async def get_articles(self, category: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get articles with caching, RSS live pull, and comprehensive fallback."""
        now = time.time()
        
        # Check cache
        if not self._cache or (now - self._cache_timestamp) > self._cache_ttl_seconds:
            articles = list(ALL_ARTICLES)
            
            # Try fetching live RSS in background if network is active
            try:
                async with httpx.AsyncClient(headers={"User-Agent": "BetweenNewsReader/1.0"}) as client:
                    tasks = [self.fetch_rss_feed(client, feed) for feed in RSS_FEEDS]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for res in results:
                        if isinstance(res, list) and res:
                            articles.extend(res)
            except Exception:
                # Network not available or external feed error: fallback operates 100% seamlessly
                pass

            self._cache["articles"] = articles
            self._cache_timestamp = now

        all_items = self._cache.get("articles", ALL_ARTICLES)

        # Apply category filter
        if category and category.lower() != "all":
            all_items = [a for a in all_items if a.get("category", "").lower() == category.lower()]

        # Apply search query
        if search:
            query = search.lower().strip()
            all_items = [
                a for a in all_items
                if query in a.get("title", "").lower() or query in a.get("summary", "").lower() or query in a.get("category", "").lower()
            ]

        return all_items

    async def get_article_by_id(self, article_id: str) -> Optional[Dict[str, Any]]:
        articles = await self.get_articles()
        for art in articles:
            if art.get("id") == article_id:
                return art
        return None

news_service = NewsService()
