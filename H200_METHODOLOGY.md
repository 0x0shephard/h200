# H200 GPU Index Pricing Methodology Report


## Executive Summary

The market for high-performance AI compute infrastructure built on NVIDIA's Hopper architecture represents a critical layer of global AI development capacity. However, this market remains characterized by fragmented pricing, opaque discount structures, and a fundamental absence of standardized benchmarks for price discovery. This creates significant inefficiencies for enterprise buyers, infrastructure operators, and investors seeking to understand true market pricing dynamics.

This document establishes a comprehensive, rigorous, and reproducible methodology for creating a standardized benchmark for H200 GPU compute. The primary output is the **H200 Compute Index Price**, a single, volume-weighted, and revenue-adjusted value representing the fair market price of one hour of H200 GPU compute. Our analysis synthesizes data from a comprehensive set of qualified cloud providers globally, spanning both hyperscale cloud platforms and specialized AI infrastructure operators.

Drawing from established methodologies in commodity markets such as NYMEX and ICE for crude oil, natural gas, and electricity futures, our approach prioritizes transparency, procedural rigor, and statistical validity. We explicitly address the market's defining characteristic: the substantial delta between public list prices and privately negotiated enterprise contracts. Our methodology incorporates discount rate models derived from market intelligence, enterprise contract analysis, and historical pricing patterns.

The methodology employs a **two-tiered weighting model** that reflects the structural composition of the H200 market, distinguishing between hyperscale providers with dominant market share and specialized providers serving niche segments. Within each tier, providers are weighted proportionally by their estimated quarterly GPU-specific revenue, ensuring the index reflects the economic gravity of each market participant.

Hyperscaler prices are adjusted using a discount blend model to reflect actual enterprise transaction economics, incorporating both volume discounts and the distribution of pricing across contract types. The resulting H200 Compute Index Price provides foundational infrastructure for the development of sophisticated financial instruments including spot pricing, forward contracts, and futures markets.

---

## Scope and Objectives

### Scope

The scope of this methodology is precisely defined to ensure focus, analytical integrity, and benchmark reliability:

**Asset Class:** Exclusively GPU-based cloud compute capacity utilizing NVIDIA's H200 Tensor Core GPU with HBM3e memory. Does not consider previous-generation GPUs, CPUs, TPUs, or other AI accelerators.

**Hardware Specification:** Confined to the NVIDIA H200 Tensor Core GPU with standard memory configuration, representing NVIDIA's highest-performance Hopper-generation AI accelerator.

**Service Type:** Covers Infrastructure-as-a-Service (IaaS) offerings where customers rent raw GPU compute hours on a pay-per-use basis. Excludes Platform-as-a-Service (PaaS), serverless inference APIs, or Software-as-a-Service (SaaS) offerings.

**Provider Universe:** Encompasses a comprehensive set of qualified cloud providers offering public access to H200 GPU infrastructure, including hyperscalers and specialized providers across global markets.

**Geographic Scope:** Data collection encompasses providers operating globally across major regions. All pricing data is normalized to United States Dollars (USD) for direct comparability.

**Time Unit:** The fundamental unit of measure is the price per GPU-hour, denominated in USD ($/GPU-Hour).

### Primary Objectives

**To Establish a Definitive Price Index:** Calculate and publish a single, reliable, and representative index price for one hour of H200 GPU compute that accurately reflects real-world market dynamics across the global provider ecosystem.

**To Ensure Reproducibility and Transparency:** Document a complete, step-by-step procedure that can be independently replicated by third parties for verification, auditability, and validation of index integrity.

**To Support Financial Product Development:** Produce a benchmark of sufficient quality and reliability to serve as the underlying reference for financial instruments, including spot exchanges, forward contracts, and futures markets.

**To Improve Market Efficiency:** Reduce information asymmetry between buyers and sellers by providing a trusted, data-driven benchmark grounded in actual market pricing and weighted by economic transaction volume.

**To Enable Comparative Analysis:** Provide a standardized reference point for evaluating H200 pricing relative to previous-generation hardware, tracking market evolution over time, and assessing competitive positioning across providers.

**To Automate Data Collection:** Deploy robust, automated scraping infrastructure capable of collecting pricing data from the provider universe on a continuous basis with minimal human intervention.

---

## Methodology Overview

### Provider Classification and Categorization

All qualified providers are classified into two categories based on infrastructure scale, revenue concentration, and market positioning:

#### Hyperscalers

Large-scale cloud service providers characterized by:
- Massive global data center infrastructure with multi-region presence
- Significant market revenue concentration
- Enterprise-focused pricing models with substantial discounts for committed use
- Support for frontier AI model training and largest-scale workloads

The hyperscaler category includes major cloud platforms with established market presence and significant infrastructure investment.

#### Neoclouds

Specialized and regional cloud compute providers not designated as Hyperscalers, characterized by:
- Focus on AI/ML workloads or GPU-specific infrastructure
- Competitive pricing structures
- Flexible deployment options
- Regional specialization or innovative infrastructure models

This category encompasses specialized AI infrastructure providers, emerging platforms, and regional operators serving specific market segments.

### Data Collection Framework

For each qualified provider, a standardized set of data points is collected through automated scraping infrastructure:

#### Provider Metadata
- Provider name and official website
- Headquarters location and operating regions
- Company status and market maturity indicators

#### Financial Intelligence
- Quarterly GPU-specific revenue estimates
- Annual recurring revenue for market sizing
- Infrastructure scale metrics

#### Pricing Data
- Public on-demand hourly price per GPU-hour
- Instance type specifications
- GPU count per instance configuration
- Hardware configuration details
- Availability type designations
- Regional pricing variations
- Currency denomination

#### Discounting Structure (Hyperscalers Only)
- Provider-specific discount rate ranges
- Volume share estimates across pricing tiers
- Discount blend formula parameters
- Update frequency protocols

### Data Sources and Validation

Data is sourced from authoritative channels using a hierarchical prioritization framework:

#### Primary Sources

**Official Financial Documents:**
- Regulatory filings for public companies
- Earnings releases and investor materials
- Annual reports and disclosures

**Official Company Disclosures:**
- Provider pricing pages and documentation
- Official APIs and calculators
- Press releases and announcements
- Technical documentation

#### Secondary Sources

**Business Intelligence Platforms:**
- Third-party data providers for private company estimates
- Market research and analyst reports

**Industry Research:**
- Specialized infrastructure market intelligence
- Pricing aggregators and comparison platforms

**Automated Web Scraping:**
- Python-based scraping infrastructure
- Multi-method fallback approach
- Regular execution schedule
- Comprehensive data validation

#### Validation Protocol

**Cross-Reference Verification:**
- All data points validated against multiple independent sources
- Official disclosures prioritized over estimates
- Discrepancy investigation and resolution

**Quality Assurance:**
- Automated range validation
- Temporal consistency checks
- Change detection and alerting
- Sample verification protocols

**Conservative Estimation:**
- Uncertainty-aware estimation practices
- Documentation of estimate ranges
- Systematic handling of missing data

### Weighting Model

A **two-tiered weighting model** ensures the index accurately reflects market structure and transaction volume:

#### Tier 1: Categorical Weighting

The index assigns differential weights to the two provider categories based on their relative market size and transaction volume. Hyperscalers receive majority weight reflecting their dominant infrastructure position, while neoclouds receive the remaining weight representing the specialized provider ecosystem.

#### Tier 2: Revenue-Proportional Weighting

Within each category, individual providers are weighted proportionally by their estimated quarterly GPU-specific revenue. This approach ensures:
- Index reflects economic gravity of each participant
- Prevention of distortion from minimal-impact providers
- Alignment with actual transaction volume
- Dynamic adjustment capability as market evolves

### Hyperscaler Discount Adjustment

The final effective price for hyperscalers incorporates a **discount blend model** reflecting the bifurcation between public list prices and enterprise contract pricing:

#### Discount Rate Range

Discount rates are derived from analysis of:
- Committed use discount structures
- Enterprise contract intelligence
- Historical pricing pattern analysis
- Provider-specific market positioning

#### Volume Split Model

The model distinguishes between:
- Discounted volume under enterprise and committed use contracts
- Full-price volume for on-demand and spot usage

#### Blended Effective Price Formula

```
Effective_Price = (List_Price × (1 - Discount_Rate)) × Volume_Discounted_Pct
                + (List_Price) × Volume_Full_Price_Pct
```

#### Discount Data Sources

**Primary Intelligence:**
- Publicly documented discount schedules
- Provider pricing program structures
- Enterprise contract frameworks

**Secondary Intelligence:**
- Enterprise procurement research
- Industry community intelligence
- Benchmark databases
- Historical pattern analysis

**Update Protocol:**
- Regular review cycles
- Emergency updates for material changes
- Documentation of all modifications
- Historical parameter archival

### Index Calculation Process

The index is calculated through a systematic multi-step process executed on a regular automated schedule:

#### Step 1: Data Aggregation

**Automated Scraping Pipeline:**
- Execute provider-specific scraper scripts
- Multiple extraction method attempts per provider
- Defined timeout parameters
- Standardized JSON output format

**Data Validation:**
- Format compliance verification
- Range validation protocols
- Completeness checks
- Duplicate detection

**Aggregation:**
- Combination of individual provider data
- Extraction of normalized prices
- Provider availability tracking
- Data quality flagging

#### Step 2: Discount Application

**Hyperscaler Processing:**
- Apply discount rate models
- Calculate blended effective prices

**Neocloud Processing:**
- Utilize public list prices
- No discount modeling applied

#### Step 3: Weight Calculation

**Category Weights:**
- Assign total weights to each category

**Individual Provider Weights:**
- Calculate revenue-proportional weights within categories
- Normalize to category totals

**Weight Normalization:**
- Handle missing provider data
- Maintain category proportions
- Document redistribution events

#### Step 4: Weighted Summation

**Index Calculation:**
- Multiply effective prices by weights
- Sum weighted contributions
- Track component contributions

#### Step 5: Validation and Quality Control

**Statistical Validation:**
- Compare against statistical measures
- Deviation threshold monitoring
- Outlier flagging

**Calculation Verification:**
- Weight sum validation
- Component ratio verification
- Intermediate calculation checks

**Historical Consistency:**
- Deviation analysis against historical values
- Anomaly detection protocols
- Investigation triggers

#### Step 6: Publication and Archival

**Data Storage:**
- Write to structured database
- Include comprehensive metadata
- Version tracking

**Artifact Archival:**
- Preserve calculation artifacts
- Maintain audit trails
- Code version references

**Transparency:**
- Document all parameters
- Preserve intermediate calculations
- Timestamp all operations

### Contingency and Fallback Protocols

#### Provider Data Unavailability

When provider data cannot be retrieved:

**Weight Redistribution:**
- Proportional redistribution within category
- Maintenance of category totals
- Documented redistribution events

**Category Preservation:**
- Cross-category isolation
- Continuity protocols
- Alert mechanisms

#### Data Quality Issues

**Invalid Data Handling:**
- Exclusion from current cycle
- Investigation flagging
- Re-inclusion criteria

**Outlier Management:**
- Deviation detection
- Verification protocols
- Temporary exclusion procedures

#### Market Disruptions

**Material Event Response:**
- Emergency review triggers
- Update protocols
- Documentation requirements
- Continuity maintenance

### Quality Assurance and Control

#### Automated Validation

**Data Validation:**
- Schema compliance
- Range checks
- Field presence verification
- Format consistency

**Calculation Validation:**
- Weight verification
- Ratio checks
- Range validation

**System Health:**
- Success rate monitoring
- Performance tracking
- Error rate analysis
- Connection verification

#### Manual Review

**Regular Review:**
- Outlier investigation
- Pattern analysis
- Provider monitoring

**Periodic Validation:**
- Sample verification
- Universe updates
- Weight calibration

**Comprehensive Audit:**
- Parameter review
- Estimate updates
- Compliance verification
- Independent validation

#### Reproducibility

**Version Control:**
- Code repository management
- Workflow versioning
- Dependency management

**Parameter Documentation:**
- Explicit parameter specification
- Historical preservation
- Change logging

**Environment Management:**
- Containerization support
- Environment reproducibility
- Dependency specification

### Uncertainty and Limitations

#### Sources of Uncertainty

**Revenue Estimates:**
- Private company estimation challenges
- Attribution complexity for diversified providers
- Mitigation through cross-validation

**Discount Rate Models:**
- Limited public disclosure of actual rates
- Continuous refinement approach
- Validation methodologies

**Market Development Stage:**
- Early deployment phase characteristics
- Limited historical data availability
- Volatility considerations

**Provider Universe:**
- Evolving market landscape
- Discovery and integration lag

#### Key Limitations

**Market Coverage:**
- Spot pricing incorporation
- Geographic aggregation
- Provider universe completeness

**Non-Price Factors:**
- Exclusion of service quality metrics
- Performance characteristics
- Support considerations

**Temporal Characteristics:**
- Periodic calculation frequency
- Snapshot methodology

**Transaction Visibility:**
- Private contract opacity
- Model-based adjustments

#### Risk Mitigation

**Data Quality:**
- Multi-source validation
- Conservative practices
- Continuous re-validation

**Methodology Robustness:**
- Regular review cycles
- Transparent documentation
- Verification protocols

**Market Coverage:**
- Continuous monitoring
- Regular updates
- Fallback mechanisms

---

## Index Applications

The H200 Compute Index is designed to support multiple critical market functions:

### Financial Products

**Spot Exchange Pricing:**
- Reference pricing for spot markets
- Dynamic pricing foundations
- Price discovery support

**Forward Contracts:**
- Benchmark for term agreements
- Risk reduction tools
- Planning enablement

**Futures Markets:**
- Underlying benchmark
- Hedging capabilities
- Liquidity provision

**Options Pricing:**
- Reference point for derivatives
- Volatility modeling
- Capacity reservation tools

### Procurement and Planning

**Vendor Evaluation:**
- Quote benchmarking
- Market comparison
- Negotiation context

**Budget Planning:**
- Cost projection
- Scenario modeling
- Allocation frameworks

**Contract Negotiation:**
- Market-informed basis
- Discount validation
- Competitiveness tracking

### Market Analysis

**Price Discovery:**
- Information asymmetry reduction
- Transparency provision
- Access democratization

**Trend Monitoring:**
- Evolution tracking
- Pressure identification
- Historical comparison

**Competitive Analysis:**
- Provider benchmarking
- Value identification
- Market share insights

### Investment and Financing

**Infrastructure Finance:**
- ROI modeling
- Financing underwriting
- Business case validation

**Asset Valuation:**
- Mark-to-market frameworks
- Secondary market pricing
- Decision analysis

**Market Intelligence:**
- Market sizing
- Growth tracking
- Investment diligence

---

## Technical Implementation

### Automated Scraping Infrastructure

**Technology Stack:**
- Python-based implementation
- HTTP client libraries
- HTML parsing frameworks
- JavaScript rendering capabilities
- Cloud database integration
- Workflow automation platform

**Scraper Architecture:**

Each provider has a dedicated scraper implementing:
- Primary extraction methods
- Fallback mechanisms
- Validation procedures
- Normalization logic
- Standardized output

**Execution Flow:**
- Sequential method attempts
- Validation at each stage
- Fallback protocol execution
- Output standardization

### Orchestration Pipeline

**Automated Workflow:**
- Regular execution schedule
- Multi-step process
- Timeout management
- Artifact preservation
- Summary reporting

**Pipeline Stages:**
- Environment preparation
- Scraper execution
- Index calculation
- Database storage
- Artifact archival
- Result logging

### Data Storage and Accessibility

**Primary Database:**
- Cloud-based data storage
- Structured schema
- Metadata preservation
- Query capabilities

**Schema Design:**
- Primary metrics
- Component tracking
- Provider details
- Calculation metadata
- Temporal tracking

**Access Patterns:**
- API endpoints
- Historical queries
- Real-time updates

---

## Methodology Governance

### Version Control

**Versioning Framework:**
- Semantic versioning scheme
- Change categorization
- Documentation requirements

**Change Management:**
- Version history
- Effective date tracking
- Rationale documentation
- Impact analysis
- Historical preservation

### Update Frequency

**Index Calculation:**
- Regular automated schedule

**Methodology Review:**
- Periodic comprehensive reviews
- Ad-hoc emergency updates
- Annual comprehensive audits

**Parameter Updates:**
- Regular review cycles
- Evidence-based modifications
- Documentation requirements

**Provider Universe:**
- Continuous monitoring
- Regular reviews
- Timely additions

### Transparency and Disclosure

**Public Documentation:**
- Complete methodology specification
- Code accessibility
- Procedure documentation
- Explicit assumptions

**Data Access:**
- Historical data availability
- Aggregate information
- Audit trail access

**Reproducibility:**
- Version control
- Environment specification
- Parameter archival
- Verification protocols

### Validation and Auditing

**Internal Validation:**
- Automated cycle validation
- Regular manual reviews
- Independent verification

**External Validation:**
- Third-party audit frameworks
- Community feedback mechanisms
- Peer review processes

**Acceptance Criteria:**
- Variance thresholds
- Validation tolerances
- Consistency requirements

---

## Conclusion

This methodology establishes a rigorous, transparent, and reproducible framework for calculating a trusted benchmark price for H200 GPU compute. By addressing fundamental market inefficiencies through systematic data collection, revenue-weighted aggregation, and discount-adjusted pricing models, the H200 Compute Index provides essential infrastructure for market efficiency, risk management, and financial product development.

The methodology draws from proven commodity market practices while adapting to the unique characteristics of the nascent H200 market. Through continuous refinement, expansion of the provider universe, and rigorous quality assurance protocols, the index will evolve to maintain accuracy and representativeness as the market matures.

Key differentiators of this methodology include:

- Comprehensive provider coverage across market segments
- Revenue-weighted accuracy reflecting transaction volume
- Discount-adjusted pricing capturing enterprise economics
- Automated resilience with systematic fallback protocols
- Transparent reproducibility through open documentation
- Continuous operation with regular update cycles
- Robust quality assurance and validation frameworks

The H200 Compute Index provides market participants with a reliable, data-driven benchmark enabling informed decisions, efficient capital allocation, and the development of sophisticated financial instruments for GPU compute capacity.

---

.


