<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a id="readme-top"></a>

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]

<br />
<div align="center">
  <a href="https://github.com/arryllopez/sharpeye.ai">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">SharpEye.ai</h3>

  <p align="center">
    AI-powered NBA player points forecast prediction platform using machine learning and Monte Carlo simulations
    <br />
    <a href="https://github.com/arryllopez/sharpeye.ai"><strong>Explore the docs »</strong></a>
    <br /><br />
    <a href="https://github.com/arryllopez/sharpeye.ai">View Demo</a>
    &middot;
    <a href="https://github.com/arryllopez/sharpeye.ai/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    &middot;
    <a href="https://github.com/arryllopez/sharpeye.ai/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>

---

## Table of Contents

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#about-the-project">About The Project</a></li>
    <li><a href="#built-with">Built With</a></li>
    <li><a href="#getting-started">Getting Started</a></li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

---

## About The Project

[![SharpEye.ai Screen Shot][product-screenshot]](https://sharpeye.ai)

SharpEye.ai is an AI-powered sports prediction analytics platform that predicts NBA player points using XGBoost machine learning models and Monte Carlo simulations. The platform analyzes historical player performance, opponent defensive stats, rest days, home/away splits, and real-time odds to provide data-driven points forecasts with confidence intervals.

This project aims to model uncertain future outcomes using historical data, quantifying risk by assigning probabilities to each possible result.

### Key Features

- Real-time NBA game and player prop data via TheOdds API
- XGBoost ML model trained on historical NBA game logs (110K+)
- Monte Carlo simulation (10,000 iterations) for probability distributions
- PostgreSQL database hosted on Supabase
- Automated daily ETL pipelines for data ingestion, transformation, and feature computation
- React frontend for intuitive user experience

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Built With

- [![FastAPI][FastAPI]][FastAPI-url]
- [![React][React.js]][React-url]
- [![PostgreSQL][PostgreSQL]][PostgreSQL-url]
- [![Supabase][Supabase]][Supabase-url]
- [![Python][Python]][Python-url]
- [![Vercel][Vercel]][Vercel-url]
- [![AWS][AWS]][AWS-url]
- [![Pandas][Pandas]][Pandas-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL (Supabase)
- TheOdds API key

### Installation

1. Get a free API Key at https://the-odds-api.com  
2. Clone the repo
   ```sh
   git clone https://github.com/arryllopez/sharpeye.ai.git
