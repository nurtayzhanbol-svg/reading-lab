"""Synthetic sample corpus. Publications and articles are fictional; figures are illustrative.
Analyses are hand-curated (as an LLM would produce them) so cross-document features can be demonstrated offline."""

R, AI, EN, GLP, BN = "European rearmament", "AI infrastructure", "Energy transition", "GLP-1 drugs", "Industrial bottlenecks"

THEMES = [
    (R, "Europe's shift to higher defence spending, its funding and its industrial base.", "active", "user"),
    (AI, "Data centres, compute capex, and the physical inputs the AI build-out depends on.", "active", "user"),
    (EN, "Decarbonisation of power and industry; grids, renewables, nuclear.", "active", "user"),
    (GLP, "GLP-1 weight-loss drugs: adoption, prices, supply and economic side-effects.", "active", "user"),
    (BN, "Physical supply constraints (grid connections, transformers, skilled labour, long-term contracts) "
         "recurring across defence, AI and energy.", "suggested", "ai"),
]


def O(key, type, epi, conf, mod, signal, statement, quote, ents="", dim="", themes=None):
    return dict(key=key, type=type, epistemic={"F": "source_fact", "A": "author_interpretation", "I": "ai_inference"}[epi],
                confidence=conf, modality=mod, signal=signal, statement=statement, quote=quote,
                entities=[{"name": e.split(":")[0], "kind": e.split(":")[1]} for e in ents.split(",") if e],
                dimension=dim, themes=themes)


ARTICLES = []


def A(**kw):
    ARTICLES.append(kw)


A(slug="m25-def", publication="The Meridian", date="2025-11-14", author="Defence correspondent",
  title="Europe's defence debate finally gets serious", themes=[R],
  text="""For three decades Europe treated defence as a line item to be trimmed. That habit is now under open attack. At a meeting of defence ministers in Brussels this week, governments discussed raising military spending well beyond NATO's 2% guideline, with several ministers floating a target of 3% of GDP by the end of the decade.

The reason is not hard to find. Russia's war in Ukraine has entered its fourth year, and doubts about America's commitment to European security have grown with every round of American budget politics. One senior diplomat put it bluntly: Europe can no longer assume that Washington will fill the gaps it leaves.

Talk is cheaper than tanks. Only a handful of countries, led by Poland and the Baltic states, already spend more than 3%. Germany, France and Italy remain below or close to 2%, and none has yet put a larger figure into a budget law. Finance ministers, facing high debt and ageing populations, have been notably quieter than their defence colleagues.

There is also the question of what money would buy. Europe's arms industry is fragmented across dozens of national champions, many of which have spent years running production lines at low rates. The European Commission estimates that the continent could produce roughly 1m artillery shells this year, far short of Ukraine's needs. Officials say they expect output to reach 2m shells a year by the end of 2026.

If the money does arrive, the beneficiaries will not only be defence firms. Rearmament on this scale would draw on steel, explosives, electronics and skilled engineers, sectors that are already tight. Whether Europe can spend more without simply bidding up prices is a question few ministers have yet tried to answer.""",
  thesis="European governments have started to discuss defence spending well above NATO's 2% guideline, but the money is not yet budgeted and the industrial base may not be able to absorb it.",
  dims=[("institutional incentives", "Defence and finance ministries pull in different directions."),
        ("industrial capacity", "Whether a fragmented arms industry can turn money into output."),
        ("geopolitical incentives", "Doubts about the US guarantee drive the debate."),
        ("economic mechanisms", "Extra demand into tight sectors may raise prices rather than volumes.")],
  obs=[
    O("a", "event", "F", .9, "discussed", "european defence spending", "European defence ministers discussed raising military spending well beyond NATO's 2% guideline, with some floating 3% of GDP by 2030.", "governments discussed raising military spending well beyond NATO's 2% guideline", "NATO:organization,Brussels:place", "institutional incentives"),
    O("b", "assumption", "A", .8, "doubted", "us security guarantee", "European policy now starts from the assumption that the US will no longer fill Europe's defence gaps.", "Europe can no longer assume that Washington will fill the gaps it leaves", "United States:country", "geopolitical incentives"),
    O("c", "evidence", "F", .9, None, "european defence spending", "Only Poland and the Baltic states already spend more than 3% of GDP; Germany, France and Italy are at or below about 2%.", "Only a handful of countries, led by Poland and the Baltic states, already spend more than 3%.", "Poland:country,Germany:country,France:country,Italy:country"),
    O("d", "uncertainty", "A", .75, "discussed", "european defence spending", "No major government has yet written a higher defence figure into a budget law; finance ministers are cautious.", "none has yet put a larger figure into a budget law", "", "fiscal constraints"),
    O("e", "evidence", "F", .85, None, "artillery shell production", "Europe can produce roughly 1m artillery shells a year, far short of Ukraine's needs.", "the continent could produce roughly 1m artillery shells this year", "European Commission:organization,Ukraine:country", "industrial capacity"),
    O("f", "prediction", "F", .8, "proposed", "artillery shell production", "Officials expect European shell output to reach 2m a year by the end of 2026.", "Officials say they expect output to reach 2m shells a year by the end of 2026", "European Commission:organization", "industrial capacity"),
    O("g", "claim", "A", .8, "discussed", "defence industrial capacity", "Europe's arms industry is fragmented into national champions running lines at low rates.", "Europe's arms industry is fragmented across dozens of national champions", "", "industrial capacity"),
    O("h", "implication", "A", .7, None, "defence industrial capacity", "Rearmament would compete for steel, explosives, electronics and engineers in already tight sectors.", "Rearmament on this scale would draw on steel, explosives, electronics and skilled engineers, sectors that are already tight", "", "second-order effects"),
    O("i", "question", "A", .7, None, "defence inflation", "Can Europe spend more on defence without simply bidding up prices?", "Whether Europe can spend more without simply bidding up prices is a question few ministers have yet tried to answer"),
    O("j", "implication", "I", .6, None, "defence industrial capacity", "If budgets rise faster than production capacity, much of the extra money may become price inflation for defence goods rather than more equipment.", "Whether Europe can spend more without simply bidding up prices", "", "economic mechanisms"),
  ])

A(slug="l26-def", publication="The Northern Ledger", date="2026-02-20", author="Europe editor",
  title="From pledges to budgets: Europe's defence money arrives", themes=[R],
  text="""What was talk in November is now law in several capitals. Germany's parliament this month approved a special defence fund of EUR 100bn on top of its regular budget, and the government committed to reaching 3% of GDP by 2029. Poland has budgeted 4.7% for this year, the highest share in NATO.

The shift has been driven as much by Washington as by Moscow. Senior American officials have repeatedly said that Europe must take primary responsibility for its own conventional defence. European governments, rather than waiting to discover whether this is rhetoric, have chosen to act as if it is policy.

How to pay is the harder question. Germany has loosened its constitutional debt brake for defence. Other governments with less fiscal room, including Italy and Spain, have hinted at cuts elsewhere. Unions and opposition parties warn that welfare budgets will be squeezed to pay for weapons, a trade-off that may test public support once the sense of emergency fades.

The European Commission has proposed a joint procurement scheme, backed by EUR 150bn in loans, to encourage governments to buy together and to buy European. Supporters argue that common orders would let manufacturers plan longer production runs. Sceptics note that national governments have rarely been willing to give up control of defence purchases.

Much of the new money will, at least at first, buy American. European firms cannot yet supply air defence systems or fighter jets in the quantities governments want, and the most urgent orders are being placed where delivery is fastest.""",
  thesis="Defence spending has moved from talk to budget law, but funding trade-offs, weak joint procurement and dependence on US suppliers will shape what it buys.",
  dims=[("fiscal trade-offs", "Debt brakes, welfare cuts and who pays."),
        ("political sustainability", "Whether public support survives once urgency fades."),
        ("institutional incentives", "National control versus joint EU procurement."),
        ("industrial capacity", "Where the money is spent depends on who can deliver.")],
  obs=[
    O("a", "event", "F", .9, "committed", "european defence spending", "Germany approved a EUR 100bn special defence fund and committed to 3% of GDP by 2029.", "Germany's parliament this month approved a special defence fund of EUR 100bn on top of its regular budget", "Germany:country", "fiscal trade-offs"),
    O("b", "evidence", "F", .9, "committed", "european defence spending", "Poland has budgeted 4.7% of GDP for defence, the highest share in NATO.", "Poland has budgeted 4.7% for this year, the highest share in NATO", "Poland:country,NATO:organization"),
    O("c", "argument", "A", .75, "doubted", "us security guarantee", "European governments are acting as if US disengagement is policy rather than rhetoric.", "European governments, rather than waiting to discover whether this is rhetoric, have chosen to act as if it is policy", "United States:country", "geopolitical incentives"),
    O("d", "event", "F", .85, "implemented", "defence funding model", "Germany loosened its constitutional debt brake to fund defence.", "Germany has loosened its constitutional debt brake for defence", "Germany:country", "fiscal trade-offs"),
    O("e", "counterargument", "A", .7, None, "defence funding model", "Unions and opposition parties warn that welfare budgets will be cut to pay for weapons.", "Unions and opposition parties warn that welfare budgets will be squeezed to pay for weapons", "Italy:country,Spain:country", "political sustainability"),
    O("f", "uncertainty", "A", .7, None, "public support for defence spending", "Public support may weaken once the sense of emergency fades.", "a trade-off that may test public support once the sense of emergency fades", "", "political sustainability"),
    O("g", "event", "F", .85, "proposed", "joint european procurement", "The European Commission proposed a EUR 150bn loan-backed joint procurement scheme to buy together and buy European.", "The European Commission has proposed a joint procurement scheme, backed by EUR 150bn in loans", "European Commission:organization", "institutional incentives"),
    O("h", "counterargument", "A", .7, "doubted", "joint european procurement", "National governments have rarely been willing to give up control of defence purchases.", "Sceptics note that national governments have rarely been willing to give up control of defence purchases", "", "institutional incentives"),
    O("i", "prediction", "A", .75, "committed", "buy european vs buy american", "Much of the new defence money will initially be spent on American equipment.", "Much of the new money will, at least at first, buy American", "United States:country", "industrial capacity"),
    O("j", "implication", "I", .6, None, "defence industrial capacity", "Because early orders go to whoever delivers fastest, European industrial capacity will lag behind budget increases.", "the most urgent orders are being placed where delivery is fastest", "", "industrial capacity"),
  ])

A(slug="m26-arms", publication="The Meridian", date="2026-05-29", issue="The Meridian, 30 May 2026", author="Industry correspondent",
  title="Europe's arms factories cannot keep up", themes=[R],
  text="""Europe's governments have found the money. Its factories have not found the capacity. Order books at the continent's biggest munitions makers now stretch to 2029, and executives say the main constraint is no longer demand but the ability to build.

Shell production illustrates the problem. Output has risen to an estimated 1.4m rounds a year, a big improvement, but new plants take two to three years to build and certify. Rheinmetall, Europe's largest shell maker, says a factory it began building in Lower Saxony last year will not reach full output until 2027.

The bottlenecks lie deep in supply chains. Nitrocellulose, a key propellant ingredient, comes from a handful of suppliers. Skilled welders and machinists are scarce, and defence firms compete for them with carmakers and energy companies. Factory managers also complain about grid connections: new plants have waited more than a year for high-voltage hookups, as transformer makers struggle with orders from wind farms and data centres.

Energy costs add to the strain. Explosives and steel are energy-intensive, and European industrial electricity remains roughly twice as expensive as in America. Industry plans assume that power will be available at competitive prices, an assumption that looks fragile.

Governments could ease the squeeze by signing longer contracts. Firms will not build plants for orders that might vanish after the next election, and most contracts still run for only two or three years. Until procurement shifts to multi-year commitments, the gap between budgets and output is likely to persist.""",
  thesis="Money is no longer the constraint on European rearmament; physical capacity is, from propellant and skilled labour to grid connections and energy costs.",
  dims=[("industrial capacity", "Production lead times and supply-chain chokepoints."),
        ("infrastructure dependencies", "Grid connections and electricity prices shared with other sectors."),
        ("institutional incentives", "Short contracts discourage investment in new plants."),
        ("labour markets", "Competition for skilled trades.")],
  obs=[
    O("a", "claim", "A", .9, "constrained", "defence industrial capacity", "The binding constraint on European rearmament is now production capacity, not money.", "the main constraint is no longer demand but the ability to build", "", "industrial capacity"),
    O("b", "evidence", "F", .85, "implemented", "artillery shell production", "European shell output has risen to about 1.4m rounds a year.", "Output has risen to an estimated 1.4m rounds a year", "", "industrial capacity"),
    O("c", "fact", "F", .85, "constrained", "defence industrial capacity", "New munitions plants take two to three years to build and certify.", "new plants take two to three years to build and certify", "", "industrial capacity"),
    O("d", "prediction", "F", .8, "constrained", "artillery shell production", "Rheinmetall's new Lower Saxony shell plant will not reach full output until 2027.", "will not reach full output until 2027", "Rheinmetall:organization,Lower Saxony:place", "industrial capacity"),
    O("e", "evidence", "F", .8, "constrained", "skilled labour shortage", "Defence firms compete with carmakers and energy companies for scarce welders and machinists.", "Skilled welders and machinists are scarce", "", "labour markets"),
    O("f", "evidence", "F", .85, "constrained", "electrical equipment shortage", "New arms plants have waited over a year for grid hookups because transformer makers are swamped by wind-farm and data-centre orders.", "new plants have waited more than a year for high-voltage hookups, as transformer makers struggle with orders from wind farms and data centres", "", "infrastructure dependencies"),
    O("g", "assumption", "A", .8, None, "cheap energy assumption", "Defence industry expansion plans assume power will be available at competitive prices.", "Industry plans assume that power will be available at competitive prices", "", "infrastructure dependencies"),
    O("h", "evidence", "F", .8, None, "industrial energy costs", "European industrial electricity costs roughly twice as much as in America.", "European industrial electricity remains roughly twice as expensive as in America", "United States:country", "economic mechanisms"),
    O("i", "argument", "A", .8, "proposed", "long-term contracts unlock capacity", "Firms will only build new plants if governments sign multi-year contracts.", "Firms will not build plants for orders that might vanish after the next election", "", "institutional incentives"),
    O("j", "prediction", "A", .75, "constrained", "defence industrial capacity", "The gap between defence budgets and output will persist until procurement shifts to multi-year commitments.", "the gap between budgets and output is likely to persist", "", "industrial capacity"),
    O("k", "insight", "I", .7, "constrained", "electrical equipment shortage", "Defence factories, data centres and wind farms are competing for the same transformers and grid capacity: a shared bottleneck that is invisible when each sector is read separately.", "transformer makers struggle with orders from wind farms and data centres", "", "infrastructure dependencies", [R, AI, EN, BN]),
  ])

A(slug="atl-def", publication="Atlas Review", date="2026-09-11", author="Guest essay",
  title="The rearmament dividend that isn't", themes=[R],
  text="""A year after Europe's governments began to talk seriously about rearmament, the money is flowing. Defence budgets across the European members of NATO have risen by about a fifth in two years, and almost every government now plans to reach 3% of GDP. Yet the hoped-for revival of Europe's own defence industry is arriving more slowly than the spending.

Some targets are being met. European shell output is on course to reach about 1.8m rounds this year, close to the goal officials set in 2025. But in more complex systems, from air defence to long-range missiles, European manufacturers still deliver only a fraction of what is ordered, and more than half of major equipment contracts signed since 2024 have gone to American suppliers.

The Commission's joint procurement scheme has disappointed. Only a small share of its loans has been drawn, and most large orders are still placed nationally. Governments say joint buying is slower and gives them less control over where jobs are created.

The political mood is also shifting. Polls in Germany, Italy and Spain show support for higher defence spending falling from its peak as governments trim other budgets. A recession or a ceasefire in Ukraine could weaken the case for sustained increases.

None of this means rearmament will stall. Contracts signed now will keep factories busy for years. But the strategic aim of the effort, a Europe able to defend itself without depending on America, may be further away than the budget figures suggest. Europe is spending like a power that has decided to rearm, while still buying like a client.""",
  thesis="Europe's defence spending has risen sharply, but industrial revival, joint procurement and strategic autonomy lag far behind the budget numbers.",
  dims=[("strategic autonomy", "Spending versus independence from the US."),
        ("political sustainability", "Declining public support and possible shocks."),
        ("industrial capacity", "Simple munitions scale; complex systems do not.")],
  obs=[
    O("a", "evidence", "F", .85, "implemented", "european defence spending", "Defence budgets of European NATO members have risen by about a fifth in two years.", "Defence budgets across the European members of NATO have risen by about a fifth in two years", "NATO:organization"),
    O("b", "claim", "A", .85, "constrained", "defence industrial capacity", "Europe's own defence-industrial revival is arriving more slowly than the spending.", "the hoped-for revival of Europe's own defence industry is arriving more slowly than the spending", "", "industrial capacity"),
    O("c", "evidence", "F", .8, "implemented", "artillery shell production", "European shell output is on course for about 1.8m rounds in 2026, close to the 2025 goal.", "European shell output is on course to reach about 1.8m rounds this year", "", "industrial capacity"),
    O("d", "evidence", "F", .8, "implemented", "buy european vs buy american", "More than half of major European equipment contracts since 2024 went to American suppliers.", "more than half of major equipment contracts signed since 2024 have gone to American suppliers", "United States:country", "strategic autonomy"),
    O("e", "evidence", "F", .8, "doubted", "joint european procurement", "Little of the Commission's joint procurement loan money has been drawn; big orders remain national.", "Only a small share of its loans has been drawn, and most large orders are still placed nationally", "European Commission:organization", "institutional incentives"),
    O("f", "evidence", "F", .75, "doubted", "public support for defence spending", "Polls in Germany, Italy and Spain show support for higher defence spending falling from its peak.", "support for higher defence spending falling from its peak", "Germany:country,Italy:country,Spain:country", "political sustainability"),
    O("g", "uncertainty", "A", .7, None, "public support for defence spending", "A recession or a Ukraine ceasefire could weaken the case for sustained increases.", "A recession or a ceasefire in Ukraine could weaken the case for sustained increases", "Ukraine:country", "political sustainability"),
    O("h", "argument", "A", .8, "doubted", "european strategic autonomy", "A Europe able to defend itself without America is further away than budgets suggest.", "a Europe able to defend itself without depending on America, may be further away than the budget figures suggest", "United States:country", "strategic autonomy"),
    O("i", "insight", "A", .85, None, "buy european vs buy american", "Europe is spending like a power that has decided to rearm while buying like a client.", "Europe is spending like a power that has decided to rearm, while still buying like a client", "", "strategic autonomy"),
    O("j", "prediction", "A", .7, "committed", "defence industrial capacity", "Contracts signed now will keep European defence factories busy for years.", "Contracts signed now will keep factories busy for years", "", "industrial capacity"),
  ])

A(slug="cap-dc", publication="Capital Times", date="2025-12-05", author="Technology editor",
  title="The data-centre gold rush", themes=[AI],
  text="""The four largest American cloud companies plan to spend more than $400bn on data centres next year, a figure that would have seemed fantastical three years ago. Executives describe the outlay as the foundation of a new computing era, in which artificial intelligence models are woven into every product and service.

Investors have so far applauded. The shares of chipmakers, power-equipment suppliers and data-centre landlords have soared, and companies that once returned cash to shareholders are now borrowing to build. Microsoft, Alphabet, Amazon and Meta have each told analysts that the risk of building too little capacity outweighs the risk of building too much.

That logic rests on a simple premise: that demand for AI services will keep growing fast enough to fill the new buildings. Early revenue is encouraging. Cloud divisions report AI-related sales growing at triple-digit rates, though from a small base.

The appetite for electricity is less often discussed. Data centres consumed about 4% of America's electricity last year. Analysts at several banks forecast that AI will double data-centre power demand by 2028, requiring new generation equivalent to dozens of large power stations.

For now the money keeps coming. Our view is that the build-out, like the railway and fibre booms before it, will leave behind infrastructure of lasting value, even if some investors are disappointed along the way.""",
  thesis="Big Tech's $400bn data-centre build-out rests on durable AI demand; even if some investors lose, it will leave lasting infrastructure, though its electricity needs are under-appreciated.",
  dims=[("capital cycle", "Debt-funded capex and the risk of over-building."),
        ("demand assumptions", "Whether AI revenue grows into the capacity."),
        ("energy dependencies", "Electricity as an overlooked input.")],
  obs=[
    O("a", "evidence", "F", .9, "committed", "ai data centre capex", "The four largest US cloud companies plan to spend over $400bn on data centres in 2026.", "plan to spend more than $400bn on data centres next year", "Microsoft:organization,Alphabet:organization,Amazon:organization,Meta:organization", "capital cycle"),
    O("b", "argument", "A", .75, "committed", "ai data centre capex", "Cloud executives argue that under-building is riskier than over-building.", "the risk of building too little capacity outweighs the risk of building too much", "Microsoft:organization,Alphabet:organization,Amazon:organization,Meta:organization", "capital cycle"),
    O("c", "assumption", "A", .8, None, "demand durability", "The build-out assumes AI demand will keep growing fast enough to fill the new capacity.", "demand for AI services will keep growing fast enough to fill the new buildings", "", "demand assumptions"),
    O("d", "evidence", "F", .75, None, "ai capex returns", "AI-related cloud sales are growing at triple-digit rates from a small base.", "Cloud divisions report AI-related sales growing at triple-digit rates, though from a small base", "", "demand assumptions"),
    O("e", "evidence", "F", .85, None, "data centre power demand", "Data centres used about 4% of US electricity last year.", "Data centres consumed about 4% of America's electricity last year", "United States:country", "energy dependencies", [AI, EN]),
    O("f", "prediction", "F", .75, None, "data centre power demand", "Bank analysts forecast AI will double data-centre power demand by 2028.", "Analysts at several banks forecast that AI will double data-centre power demand by 2028", "", "energy dependencies", [AI, EN]),
    O("g", "argument", "A", .7, "committed", "ai capex returns", "Like railways and fibre, the AI build-out will leave infrastructure of lasting value even if some investors lose.", "the build-out, like the railway and fibre booms before it, will leave behind infrastructure of lasting value", "", "capital cycle"),
    O("h", "implication", "I", .6, None, "ai capex returns", "Debt-funded capex raises the cost of being wrong if AI demand disappoints.", "companies that once returned cash to shareholders are now borrowing to build", "", "capital cycle"),
    O("i", "insight", "A", .7, None, "data centre power demand", "Electricity is the under-discussed input of the AI boom.", "The appetite for electricity is less often discussed", "", "energy dependencies", [AI, EN]),
  ])

A(slug="m26-pow", publication="The Meridian", date="2026-03-13", author="Technology correspondent",
  title="Power, not chips, is AI's new bottleneck", themes=[AI],
  text="""A year ago the scarcest input for artificial intelligence was the chip. Today it is the electricity to run it. In Virginia, the world's largest data-centre market, utilities have told developers that new grid connections may take until 2030. In Texas and Arizona, projects are being designed around their own gas turbines because the grid cannot supply them in time.

The queue is not only for power stations. Transformers, switchgear and high-voltage cable are on back order, with lead times for large transformers stretching to three or four years. The same equipment is needed by wind and solar farms, by electrified factories and by grid upgrades, so data centres are competing with the energy transition for the same scarce kit.

Technology companies are responding by becoming energy companies. Several have signed long-term contracts for nuclear power, and some are discussing financing new reactors. Others are moving computation to wherever power is available, from Scandinavia to the Middle East.

The shift has consequences. Gas-fired generation built for data centres may lock in emissions that companies had pledged to eliminate. Local opposition to new transmission lines and rising household electricity bills are becoming political issues in several American states.

Most forecasts of AI's growth assume that power will be found at reasonable prices. If it is not, the pace of the AI build-out will be set less by software engineers than by utility regulators.""",
  thesis="Electricity and grid equipment, not chips, now limit the AI build-out, pushing tech firms into energy and putting AI in competition with the energy transition.",
  dims=[("infrastructure dependencies", "Grid connections and electrical equipment lead times."),
        ("climate trade-offs", "Gas generation versus decarbonisation pledges."),
        ("local politics", "Electricity bills and transmission opposition.")],
  obs=[
    O("a", "claim", "A", .85, "constrained", "data centre power demand", "Electricity has replaced chips as the scarcest input for AI.", "Today it is the electricity to run it", "", "infrastructure dependencies", [AI, EN]),
    O("b", "evidence", "F", .85, "constrained", "grid connection bottleneck", "Virginia utilities told data-centre developers that new grid connections may take until 2030.", "utilities have told developers that new grid connections may take until 2030", "Virginia:place", "infrastructure dependencies", [AI, EN]),
    O("c", "evidence", "F", .8, "implemented", "on-site gas generation", "Data centres in Texas and Arizona are being built with their own gas turbines.", "projects are being designed around their own gas turbines because the grid cannot supply them in time", "Texas:place,Arizona:place", "infrastructure dependencies", [AI, EN]),
    O("d", "evidence", "F", .85, "constrained", "electrical equipment shortage", "Lead times for large transformers have stretched to three or four years.", "lead times for large transformers stretching to three or four years", "", "infrastructure dependencies", [AI, EN]),
    O("e", "insight", "A", .8, "constrained", "electrical equipment shortage", "Data centres compete with the energy transition for the same scarce electrical equipment.", "data centres are competing with the energy transition for the same scarce kit", "", "infrastructure dependencies", [AI, EN, BN]),
    O("f", "event", "F", .8, "discussed", "nuclear power for data centres", "Tech firms have signed nuclear power contracts and are discussing financing new reactors.", "Several have signed long-term contracts for nuclear power, and some are discussing financing new reactors", "", "energy dependencies", [AI, EN]),
    O("g", "implication", "A", .75, None, "on-site gas generation", "Gas plants built for data centres may lock in emissions companies pledged to eliminate.", "Gas-fired generation built for data centres may lock in emissions that companies had pledged to eliminate", "", "climate trade-offs", [AI, EN]),
    O("h", "evidence", "F", .7, None, "electricity price politics", "Rising household electricity bills and transmission opposition are becoming political issues in US states.", "rising household electricity bills are becoming political issues in several American states", "United States:country", "local politics"),
    O("i", "assumption", "A", .8, None, "cheap energy assumption", "AI growth forecasts assume power will be found at reasonable prices.", "Most forecasts of AI's growth assume that power will be found at reasonable prices", "", "infrastructure dependencies"),
    O("j", "prediction", "A", .7, "constrained", "data centre power demand", "The pace of the AI build-out will be set by utility regulators more than by software engineers.", "the pace of the AI build-out will be set less by software engineers than by utility regulators", "", "institutional incentives"),
  ])

A(slug="m26-capex", publication="The Meridian", date="2026-05-29", issue="The Meridian, 30 May 2026", author="Finance correspondent",
  title="The AI capex bill comes due", themes=[AI],
  text="""Investors who cheered the data-centre boom are starting to ask when it will pay. The big four cloud companies are on track to spend about $450bn this year, more than they planned in December, yet revenue directly attributable to AI remains a small fraction of that sum.

Share prices have become jittery. Each quarterly report now prompts questions about depreciation, because chips bought today may be obsolete within four or five years, long before the buildings that house them. Some analysts estimate that the industry needs AI revenue several times its current level by 2030 to earn a normal return on the investment.

Executives remain unbowed. They point to rapid growth in paying business customers and argue that the cost of computing will fall, unlocking new uses. Yet the comparison with railways cuts both ways: many of the railway companies that built Britain's network went bust, even as the network itself proved valuable.

There are early signs of discipline. Two large developers have delayed projects in markets where power is unavailable, and at least one cloud company has cancelled leases for planned sites. These may be adjustments rather than retreats, but they suggest the build-out is beginning to meet limits of finance and energy at the same time.

Our judgement is that AI spending will slow in 2027, not because the technology disappoints, but because power constraints and investor patience will both run short.""",
  thesis="AI capex keeps rising while AI revenue lags; finance and energy limits are starting to bind, and spending is likely to slow in 2027.",
  dims=[("capital cycle", "Depreciation and required returns."),
        ("investor incentives", "Patience versus fear of missing out."),
        ("infrastructure dependencies", "Power availability shaping where projects go.")],
  obs=[
    O("a", "evidence", "F", .85, "implemented", "ai data centre capex", "Big Tech is on track to spend about $450bn on data centres in 2026, more than planned in December.", "The big four cloud companies are on track to spend about $450bn this year, more than they planned in December", "", "capital cycle"),
    O("b", "claim", "F", .8, "doubted", "ai capex returns", "Revenue directly attributable to AI remains a small fraction of capex.", "revenue directly attributable to AI remains a small fraction of that sum", "", "capital cycle"),
    O("c", "evidence", "A", .7, None, "ai capex returns", "AI chips may be obsolete within four or five years, long before their buildings.", "chips bought today may be obsolete within four or five years", "", "capital cycle"),
    O("d", "evidence", "A", .7, None, "ai capex returns", "Analysts estimate AI revenue must grow several-fold by 2030 for a normal return.", "the industry needs AI revenue several times its current level by 2030 to earn a normal return", "", "capital cycle"),
    O("e", "counterargument", "A", .7, "committed", "ai capex returns", "Executives argue falling compute costs will unlock new uses and demand.", "argue that the cost of computing will fall, unlocking new uses", "", "investor incentives"),
    O("f", "argument", "A", .8, "doubted", "ai capex returns", "The railway analogy cuts both ways: many railway builders went bust even though the network proved valuable.", "many of the railway companies that built Britain's network went bust, even as the network itself proved valuable", "Britain:country", "capital cycle"),
    O("g", "event", "F", .8, "doubted", "ai data centre capex", "At least one cloud company cancelled leases for planned data-centre sites.", "at least one cloud company has cancelled leases for planned sites", "", "investor incentives"),
    O("h", "insight", "A", .8, "constrained", "data centre power demand", "The AI build-out is meeting limits of finance and energy at the same time.", "the build-out is beginning to meet limits of finance and energy at the same time", "", "infrastructure dependencies", [AI, EN]),
    O("i", "prediction", "A", .7, "doubted", "ai data centre capex", "AI spending will slow in 2027 as power constraints and investor patience run short.", "AI spending will slow in 2027", "", "capital cycle"),
    O("j", "implication", "I", .6, "constrained", "grid connection bottleneck", "Project delays in power-poor markets show the grid bottleneck is already shaping where AI capacity is built.", "Two large developers have delayed projects in markets where power is unavailable", "", "infrastructure dependencies", [AI, EN]),
  ])

A(slug="l26-nuc", publication="The Northern Ledger", date="2026-08-21", author="Energy editor",
  title="Tech giants bet on nuclear to power AI", themes=[AI, EN],
  text="""The technology industry's search for electricity has reached the reactor. This summer three of the largest cloud companies signed agreements to buy power from small modular reactors, and one has agreed to help finance the restart of a closed nuclear plant in Pennsylvania. Together the deals cover more than 5 gigawatts of future capacity.

Supporters say nuclear is the only source that can deliver large amounts of constant, low-carbon power. Data centres run around the clock, and wind and solar, even with batteries, struggle to match that profile without large back-up.

The first small reactors will not produce power until the early 2030s, however, and no design has yet been built at commercial scale in the West. Cost overruns have plagued every large nuclear project in Europe and America for two decades. Critics argue that the deals are as much about public relations as about electricity.

In the meantime the data centres are being built anyway. Utilities in America report that data-centre electricity demand rose by about a quarter in the past year, and most of the new supply is coming from gas. Spending on AI infrastructure shows little sign of slowing: the big cloud companies raised their capital budgets again in July.

The deals do shift the economics of nuclear. Long-term contracts from creditworthy buyers are exactly what reactor developers have lacked. If even a few of these projects succeed, AI may end up financing a revival of nuclear power that climate policy alone could not.""",
  thesis="Big Tech's nuclear deals will not deliver power for years and gas fills the gap now, but long-term contracts could finance a nuclear revival.",
  dims=[("energy dependencies", "Firm low-carbon power for 24/7 loads."),
        ("project risk", "Unproven designs and cost overruns."),
        ("financing mechanisms", "Long-term offtake contracts as the missing ingredient.")],
  obs=[
    O("a", "event", "F", .85, "committed", "nuclear power for data centres", "Three large cloud companies signed small-modular-reactor power deals covering over 5 GW.", "three of the largest cloud companies signed agreements to buy power from small modular reactors", "Pennsylvania:place", "energy dependencies"),
    O("b", "argument", "A", .7, None, "nuclear power for data centres", "Supporters say only nuclear can deliver large amounts of constant low-carbon power.", "nuclear is the only source that can deliver large amounts of constant, low-carbon power", "", "energy dependencies"),
    O("c", "uncertainty", "F", .8, "constrained", "nuclear power for data centres", "The first small reactors will not produce power until the early 2030s.", "The first small reactors will not produce power until the early 2030s", "", "project risk"),
    O("d", "counterargument", "A", .65, "doubted", "nuclear power for data centres", "Critics see the nuclear deals as public relations as much as electricity supply.", "Critics argue that the deals are as much about public relations as about electricity", "", "project risk"),
    O("e", "evidence", "F", .85, "implemented", "data centre power demand", "US data-centre electricity demand rose by about a quarter in the past year.", "data-centre electricity demand rose by about a quarter in the past year", "United States:country", "energy dependencies"),
    O("f", "evidence", "F", .8, "implemented", "on-site gas generation", "Most new supply for data centres is coming from gas.", "most of the new supply is coming from gas", "", "energy dependencies"),
    O("g", "evidence", "F", .85, "committed", "ai data centre capex", "The big cloud companies raised their capital budgets again in July 2026.", "the big cloud companies raised their capital budgets again in July", "", "capital cycle", [AI]),
    O("h", "implication", "A", .7, None, "nuclear power for data centres", "AI demand may finance a nuclear revival that climate policy alone could not.", "AI may end up financing a revival of nuclear power that climate policy alone could not", "", "financing mechanisms"),
    O("i", "insight", "A", .75, None, "long-term contracts unlock capacity", "Long-term contracts from creditworthy buyers are what reactor developers have lacked.", "Long-term contracts from creditworthy buyers are exactly what reactor developers have lacked", "", "financing mechanisms", [AI, EN, BN]),
  ])

A(slug="l26-grid", publication="The Northern Ledger", date="2026-01-23", author="Energy editor",
  title="Europe's grid is the energy transition's weakest link", themes=[EN],
  text="""Europe has become good at building wind and solar farms. It is much worse at connecting them. Across the European Union, projects with a combined capacity of more than 500 gigawatts are waiting for grid connections, according to industry estimates, several times the capacity actually installed last year.

The problem is partly physical. Transmission lines take a decade to plan and build, and the factories that make transformers and high-voltage cable are running at full capacity. Siemens Energy and Hitachi Energy, two of the biggest suppliers, have order backlogs stretching years into the future.

It is also regulatory. Grid operators are paid to minimise costs to consumers, not to build ahead of demand, and permitting rules allow almost any line to be challenged in court. The European Commission has proposed a grid action plan, but most of the levers remain with national regulators.

New sources of demand are making the queue longer. Electrified heating, electric cars, and in some countries data centres and defence factories are all applying for connections at the same time. Ireland has effectively paused new data-centre connections around Dublin.

The transition's architects assumed that cheap renewable electricity would flow wherever it was needed. Unless grids are built faster, the more likely outcome is curtailed wind farms, higher prices and a slower transition than governments have promised.""",
  thesis="Grid connections, equipment shortages and regulatory incentives, not generation, are now the main brake on Europe's energy transition.",
  dims=[("infrastructure dependencies", "Connection queues and equipment backlogs."),
        ("regulatory incentives", "Cost-minimising grid regulation discourages anticipatory investment."),
        ("competing demand", "New loads from data centres, defence and electrification.")],
  obs=[
    O("a", "evidence", "F", .85, "constrained", "grid connection bottleneck", "More than 500 GW of EU renewable projects are waiting for grid connections.", "projects with a combined capacity of more than 500 gigawatts are waiting for grid connections", "European Union:organization", "infrastructure dependencies"),
    O("b", "evidence", "F", .85, "constrained", "electrical equipment shortage", "Transformer and high-voltage cable factories are running at full capacity.", "the factories that make transformers and high-voltage cable are running at full capacity", "", "infrastructure dependencies"),
    O("c", "evidence", "F", .8, "constrained", "electrical equipment shortage", "Siemens Energy and Hitachi Energy have multi-year order backlogs.", "Siemens Energy and Hitachi Energy, two of the biggest suppliers, have order backlogs stretching years into the future", "Siemens Energy:organization,Hitachi Energy:organization", "infrastructure dependencies", [EN, BN]),
    O("d", "argument", "A", .8, None, "grid regulation incentives", "Grid operators are rewarded for minimising consumer costs, not for building ahead of demand.", "Grid operators are paid to minimise costs to consumers, not to build ahead of demand", "", "regulatory incentives"),
    O("e", "event", "F", .8, "proposed", "grid regulation incentives", "The European Commission proposed a grid action plan, but national regulators hold most levers.", "The European Commission has proposed a grid action plan", "European Commission:organization", "regulatory incentives"),
    O("f", "insight", "A", .8, "constrained", "grid connection bottleneck", "Data centres and defence factories are joining electrification in the same grid-connection queue.", "in some countries data centres and defence factories are all applying for connections at the same time", "", "competing demand", [EN, AI, R, BN]),
    O("g", "event", "F", .85, "constrained", "grid connection bottleneck", "Ireland has effectively paused new data-centre connections around Dublin.", "Ireland has effectively paused new data-centre connections around Dublin", "Ireland:country,Dublin:place", "competing demand", [EN, AI]),
    O("h", "assumption", "A", .8, None, "cheap energy assumption", "Transition planning assumed cheap renewable electricity would flow wherever needed.", "The transition's architects assumed that cheap renewable electricity would flow wherever it was needed", "", "infrastructure dependencies"),
    O("i", "prediction", "A", .7, "constrained", "pace of energy transition", "Without faster grid building, Europe faces curtailment, higher prices and a slower transition.", "the more likely outcome is curtailed wind farms, higher prices and a slower transition than governments have promised", "", "infrastructure dependencies"),
  ])

A(slug="cap-glp", publication="Capital Times", date="2026-02-06", author="Health editor",
  title="The weight-loss drug economy", themes=[GLP],
  text="""More than 15m Americans now take a GLP-1 drug such as Wegovy or Zepbound, and the number is rising by hundreds of thousands a month. Novo Nordisk and Eli Lilly, the two makers, have become among the most valuable companies in the world.

Supply has been the main constraint. Both firms spent much of the past two years rationing doses while they built new factories, and shortages pushed many patients toward cheaper compounded copies. The companies say capacity will roughly double by the end of 2026.

The next battle will be over price. A month's supply still costs around $1,000 at list price in America. With rival drugs and pill versions due to arrive, we expect prices to fall by at least a third within two years, which would open the drugs to millions more patients.

The effects are spreading beyond medicine. Food companies report that households with a GLP-1 user buy noticeably less snack food, and some airlines have even calculated fuel savings from lighter passengers. Investors are trying to price which industries win and lose from a thinner population.

For governments, the drugs are a long-term bargain. By reducing diabetes, heart disease and joint problems, they should save health systems more than they cost over time.""",
  thesis="GLP-1 drugs are scaling fast; with supply easing and prices set to fall, their effects will spread across the economy and, the author argues, save health systems money.",
  dims=[("business implications", "Winners and losers beyond pharma."),
        ("pricing dynamics", "Competition and new formulations."),
        ("fiscal effects", "Health-system costs versus long-term savings.")],
  obs=[
    O("a", "evidence", "F", .85, "implemented", "glp-1 adoption", "More than 15m Americans take a GLP-1 drug, rising by hundreds of thousands a month.", "More than 15m Americans now take a GLP-1 drug such as Wegovy or Zepbound", "United States:country,Wegovy:product,Zepbound:product"),
    O("b", "evidence", "F", .85, "constrained", "glp-1 supply", "Novo Nordisk and Eli Lilly rationed doses for two years while building factories.", "Both firms spent much of the past two years rationing doses while they built new factories", "Novo Nordisk:organization,Eli Lilly:organization", "industrial capacity"),
    O("c", "prediction", "F", .75, "committed", "glp-1 supply", "The makers say GLP-1 capacity will roughly double by end-2026.", "The companies say capacity will roughly double by the end of 2026", "Novo Nordisk:organization,Eli Lilly:organization", "industrial capacity"),
    O("d", "evidence", "F", .85, None, "glp-1 prices", "A month of GLP-1 treatment costs around $1,000 at US list price.", "A month's supply still costs around $1,000 at list price in America", "United States:country", "pricing dynamics"),
    O("e", "prediction", "A", .7, "proposed", "glp-1 prices", "GLP-1 prices will fall by at least a third within two years.", "we expect prices to fall by at least a third within two years", "", "pricing dynamics"),
    O("f", "evidence", "F", .7, None, "glp-1 consumer effects", "Households with a GLP-1 user buy noticeably less snack food.", "households with a GLP-1 user buy noticeably less snack food", "", "business implications"),
    O("g", "prediction", "A", .65, None, "glp-1 health budget impact", "GLP-1 drugs will save health systems more than they cost over time.", "they should save health systems more than they cost over time", "", "fiscal effects"),
    O("h", "assumption", "I", .65, None, "demand durability", "The claim that the drugs pay for themselves implicitly assumes patients stay on them for many years.", "By reducing diabetes, heart disease and joint problems, they should save health systems more than they cost over time", "", "fiscal effects"),
  ])

A(slug="l26-glp", publication="The Northern Ledger", date="2026-06-19", author="Health correspondent",
  title="Weight-loss pills start a price war", themes=[GLP],
  text="""The first oral GLP-1 drug won approval in America this spring, and its maker priced it at $349 a month for patients paying cash, roughly a third of the list price of injectable versions a year ago. Within weeks, rivals cut prices on their injections.

The shortages of 2024 and 2025 are over. Novo Nordisk and Eli Lilly have both opened new plants, and American regulators removed the drugs from the official shortage list, which also ended the legal basis for most compounded copies.

Cheaper drugs mean more patients. Prescriptions grew by about 40% in the first half of the year, and employers that had refused to cover the drugs are reconsidering. Government programmes negotiated discounts that brought their cost down further.

Not everyone gains. Pharmacy benefit managers and compounding pharmacies are losing a lucrative business, and the two incumbents face lower margins than investors had assumed. Analysts now expect at least six GLP-1 drugs on the American market by 2028.

The bigger unknown is how long patients will stay on the drugs. Studies suggest that about half stop within a year, often because of side effects or cost, and most regain weight after stopping.""",
  thesis="An oral GLP-1 and the end of shortages have triggered a price war that is widening access, but adherence remains the big unknown.",
  dims=[("pricing dynamics", "Oral formulation and competition."),
        ("market structure", "Incumbents, intermediaries and new entrants."),
        ("patient behaviour", "Adherence and discontinuation.")],
  obs=[
    O("a", "event", "F", .9, "implemented", "glp-1 prices", "The first oral GLP-1 launched at $349 a month cash, about a third of last year's injectable list price.", "its maker priced it at $349 a month for patients paying cash", "United States:country", "pricing dynamics"),
    O("b", "event", "F", .85, "implemented", "glp-1 prices", "Rivals cut injectable GLP-1 prices within weeks.", "Within weeks, rivals cut prices on their injections", "", "pricing dynamics"),
    O("c", "evidence", "F", .85, "implemented", "glp-1 supply", "GLP-1 shortages are over; the drugs left the US shortage list.", "The shortages of 2024 and 2025 are over", "Novo Nordisk:organization,Eli Lilly:organization", "industrial capacity"),
    O("d", "evidence", "F", .8, "implemented", "glp-1 adoption", "GLP-1 prescriptions grew about 40% in the first half of 2026.", "Prescriptions grew by about 40% in the first half of the year", ""),
    O("e", "implication", "A", .75, None, "glp-1 prices", "Novo Nordisk and Eli Lilly face lower margins than investors assumed.", "the two incumbents face lower margins than investors had assumed", "Novo Nordisk:organization,Eli Lilly:organization", "market structure"),
    O("f", "prediction", "F", .7, None, "glp-1 competition", "At least six GLP-1 drugs are expected on the US market by 2028.", "Analysts now expect at least six GLP-1 drugs on the American market by 2028", "United States:country", "market structure"),
    O("g", "uncertainty", "A", .8, None, "demand durability", "How long patients stay on GLP-1 drugs is the biggest unknown.", "The bigger unknown is how long patients will stay on the drugs", "", "patient behaviour"),
    O("h", "evidence", "F", .75, "doubted", "demand durability", "About half of GLP-1 patients stop within a year and most regain weight.", "about half stop within a year", "", "patient behaviour"),
  ])

A(slug="m26-glp", publication="The Meridian", date="2026-09-25", author="Health correspondent",
  title="Can health systems afford the weight-loss revolution?", themes=[GLP],
  text="""Cheaper GLP-1 drugs were supposed to ease the pressure on health budgets. So far they have done the opposite. Spending on the drugs by America's public insurance programmes has tripled in two years, and Britain's health service has had to ration access despite negotiating steep discounts.

The arithmetic is simple. Even at lower prices, tens of millions of eligible patients multiplied by years of treatment produce enormous bills, while the savings from fewer heart attacks and less diabetes arrive slowly, if at all, within a budget cycle.

The savings case also assumes that patients take the drugs for years. In practice many stop, and regain the weight, which means health systems pay for treatment without banking the long-term benefit. Some economists argue that the drugs will raise total health spending for at least a decade.

Governments are responding in different ways. America is negotiating prices directly for the first time; several European countries limit prescriptions to patients with the highest risk. Denmark, home of Novo Nordisk, has seen its economy reshaped by the company's growth.

The drugs may still prove a bargain over a lifetime. But the claim that they will pay for themselves is, for now, more hope than evidence.""",
  thesis="Cheaper GLP-1s are raising, not lowering, health spending; the self-financing case depends on long adherence that is not happening.",
  dims=[("fiscal effects", "Budget-cycle costs versus lifetime savings."),
        ("patient behaviour", "Discontinuation undermines the savings case."),
        ("policy responses", "Price negotiation and rationing.")],
  obs=[
    O("a", "evidence", "F", .85, "implemented", "glp-1 health budget impact", "US public insurance spending on GLP-1s tripled in two years.", "Spending on the drugs by America's public insurance programmes has tripled in two years", "United States:country", "fiscal effects"),
    O("b", "claim", "A", .8, "doubted", "glp-1 health budget impact", "Cheaper GLP-1s have increased rather than eased pressure on health budgets.", "So far they have done the opposite", "Britain:country", "fiscal effects"),
    O("c", "argument", "A", .8, None, "glp-1 health budget impact", "Treatment costs are immediate while health savings arrive slowly, if at all, within a budget cycle.", "the savings from fewer heart attacks and less diabetes arrive slowly, if at all, within a budget cycle", "", "fiscal effects"),
    O("d", "assumption", "A", .8, None, "demand durability", "The savings case assumes patients take the drugs for years.", "The savings case also assumes that patients take the drugs for years", "", "patient behaviour"),
    O("e", "prediction", "A", .65, "doubted", "glp-1 health budget impact", "Some economists predict GLP-1s will raise total health spending for at least a decade.", "the drugs will raise total health spending for at least a decade", "", "fiscal effects"),
    O("f", "event", "F", .8, "implemented", "glp-1 prices", "The US is negotiating GLP-1 prices directly for the first time.", "America is negotiating prices directly for the first time", "United States:country", "policy responses"),
    O("g", "evidence", "F", .75, None, "novo nordisk economic weight", "Novo Nordisk's growth has reshaped Denmark's economy.", "Denmark, home of Novo Nordisk, has seen its economy reshaped by the company's growth", "Denmark:country,Novo Nordisk:organization", "business implications"),
    O("h", "insight", "A", .8, "doubted", "glp-1 health budget impact", "The claim that GLP-1s pay for themselves is more hope than evidence.", "the claim that they will pay for themselves is, for now, more hope than evidence", "", "fiscal effects"),
    O("i", "insight", "I", .6, "doubted", "demand durability", "Both the GLP-1 savings case and the AI capex case rest on assumptions of durable multi-year demand that later reporting has started to question.", "In practice many stop, and regain the weight", "", "demand assumptions", [GLP, AI]),
  ])

LINKS = [
    ("m25-def:a", "l26-def:a", "evolves", "discussed \u2192 committed in budget law"),
    ("l26-def:a", "atl-def:a", "evolves", "committed \u2192 budgets up ~20%"),
    ("m25-def:e", "m26-arms:b", "evolves", "~1m \u2192 ~1.4m shells/year"),
    ("m26-arms:b", "atl-def:c", "evolves", "~1.4m \u2192 ~1.8m shells/year"),
    ("m25-def:f", "atl-def:c", "supports", "2m-by-end-2026 target largely on track (~1.8m in 2026)"),
    ("m25-def:g", "m26-arms:a", "evolves", "fragmentation \u2192 capacity is the binding constraint"),
    ("m26-arms:a", "atl-def:b", "supports", "industrial revival lags spending"),
    ("m25-def:j", "m26-arms:a", "supports", "budgets outrun capacity"),
    ("l26-def:g", "atl-def:e", "evolves", "proposed \u2192 low take-up"),
    ("l26-def:h", "atl-def:e", "supports", "national control persisted"),
    ("l26-def:i", "atl-def:d", "supports", "more than half of major contracts went to US suppliers"),
    ("l26-def:f", "atl-def:f", "evolves", "risk \u2192 measurable decline in polls"),
    ("m26-arms:j", "atl-def:b", "supports", None),
    ("m25-def:b", "atl-def:h", "evolves", "doubts about US \u2192 autonomy still distant"),
    ("cap-dc:a", "m26-capex:a", "evolves", "$400bn planned \u2192 ~$450bn"),
    ("m26-capex:a", "l26-nuc:g", "evolves", "budgets raised again"),
    ("cap-dc:g", "m26-capex:f", "contradicts", "railway analogy: lasting value vs bankrupt builders"),
    ("cap-dc:f", "l26-nuc:e", "supports", "demand +25% in a year, consistent with doubling by 2028"),
    ("cap-dc:f", "m26-pow:a", "evolves", "demand forecast \u2192 supply constraint"),
    ("cap-dc:i", "m26-pow:a", "evolves", "under-discussed \u2192 main bottleneck"),
    ("m26-capex:g", "l26-nuc:g", "contradicts", "cancelled leases vs raised budgets"),
    ("m26-pow:f", "l26-nuc:a", "evolves", "discussed \u2192 committed (>5 GW)"),
    ("m26-pow:g", "l26-nuc:f", "supports", "new supply mostly gas"),
    ("cap-dc:c", "m26-capex:b", "contradicts", "demand assumption vs small AI revenue"),
    ("l26-grid:b", "m26-pow:d", "repeats", "transformer shortage in energy and AI"),
    ("l26-grid:b", "m26-arms:f", "repeats", "the same shortage hits arms factories"),
    ("m26-pow:e", "m26-arms:k", "supports", None),
    ("l26-grid:h", "m26-pow:i", "repeats", "cheap-power assumption"),
    ("m26-pow:i", "m26-arms:g", "repeats", "cheap-power assumption"),
    ("l26-grid:g", "m26-capex:j", "supports", None),
    ("l26-grid:f", "m26-arms:f", "supports", "defence factories in the connection queue"),
    ("m26-arms:i", "l26-nuc:i", "repeats", "long-term contracts unlock capacity in both sectors"),
    ("cap-glp:e", "l26-glp:a", "supports", "pill launched at ~1/3 of prior list price"),
    ("cap-glp:c", "l26-glp:c", "supports", "shortages ended"),
    ("cap-glp:b", "l26-glp:c", "evolves", "constrained \u2192 resolved"),
    ("cap-glp:a", "l26-glp:d", "evolves", "adoption accelerating"),
    ("cap-glp:g", "m26-glp:b", "contradicts", "savings vs rising budgets"),
    ("cap-glp:h", "l26-glp:h", "contradicts", "half stop within a year"),
    ("l26-glp:g", "m26-glp:d", "evolves", "unknown \u2192 undermines savings case"),
    ("cap-dc:c", "cap-glp:h", "repeats", "durable-demand assumption in AI and GLP-1"),
]
