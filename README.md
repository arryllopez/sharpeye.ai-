<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a id="readme-top"></a>
<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/arryllopez/sharpeye.ai">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">SharpEye.ai</h3>

  <p align="center">
    AI-powered NBA player prop prediction platform using machine learning and Monte Carlo simulations
    <br />
    <a href="https://github.com/arryllopez/sharpeye.ai"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/arryllopez/sharpeye.ai">View Demo</a>
    &middot;
    <a href="https://github.com/arryllopez/sharpeye.ai/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    &middot;
    <a href="https://github.com/arryllopez/sharpeye.ai/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

[![SharpEye.ai Screen Shot][product-screenshot]](https://sharpeye.ai)

SharpEye.ai is an AI-powered sports betting analytics platform that predicts NBA player prop outcomes using XGBoost machine learning models and Monte Carlo simulations. The platform analyzes historical player performance, opponent defensive stats, rest days, home/away splits, and real-time odds to provide data-driven betting recommendations with confidence intervals and edge calculations.

Key Features:
* Real-time NBA game and player prop data via TheOdds API
* XGBoost ML model trained on historical NBA game logs
* Monte Carlo simulation (10,000 iterations) for probability distributions
* PostgreSQL database for scalable data storage
* Automated daily data ingestion and feature calculation
* React frontend for intuitive user experience

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

* [![FastAPI][FastAPI]][FastAPI-url]
* [![React][React.js]][React-url]
* [![PostgreSQL][PostgreSQL]][PostgreSQL-url]
* [![Python][Python]][Python-url]
* [![Railway][Railway]][Railway-url]
* [![Vercel][Vercel]][Vercel-url]
* [![AWS][AWS]][AWS-url]
* [![Pandas][Pandas]][Pandas-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

To get a local copy up and running follow these steps.

### Prerequisites

* Python 3.9+
* Node.js 18+
* PostgreSQL database
* TheOdds API key

### Installation

1. Get a free API Key at [https://the-odds-api.com](https://the-odds-api.com)
2. Clone the repo
   ```sh
   git clone https://github.com/arryllopez/sharpeye.ai.git
   ```
3. Install Python dependencies
   ```sh
   cd backend
   pip install -r requirements.txt
   ```
4. Create `.env` file in `backend/` directory
   ```env
   THEODDS_API_KEY='YOUR_API_KEY'
   DATABASE_URL='postgresql://user:password@host:port/database'
   ENV='dev'
   ```
5. Run database migration
   ```sh
   python scripts/migrate_csv_to_db.py
   ```
6. Start the FastAPI backend
   ```sh
   uvicorn app.main:app --reload
   ```
7. Install frontend dependencies (when available)
   ```sh
   cd frontend
   npm install
   npm run dev
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

SharpEye.ai allows you to analyze NBA player props with AI-driven predictions:

1. Browse today's NBA games
2. Select a player and prop type (points, rebounds, assists, etc.)
3. Enter the betting line and odds from your sportsbook
4. Get instant predictions with:
   - Expected player performance
   - Over/Under probabilities
   - Confidence intervals
   - Edge calculation
   - Key factors influencing the prediction

_For more examples, please refer to the [Documentation](https://github.com/arryllopez/sharpeye.ai)_

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [x] XGBoost model training on historical data
- [x] TheOdds API integration
- [x] PostgreSQL database schema
- [x] Monte Carlo simulation engine
- [ ] Database migration completion
- [ ] Feature calculation service (PostgreSQL-based)
- [ ] /predict API endpoint
- [ ] AWS Lambda for daily automation
- [ ] FastAPI backend deployment (Railway)
- [ ] React frontend development
- [ ] Frontend deployment (Vercel)
- [ ] Multi-prop support (rebounds, assists, etc.)
    - [ ] Separate models per prop type
    - [ ] Parlay analysis

See the [open issues](https://github.com/arryllopez/sharpeye.ai/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Top contributors:

<a href="https://github.com/arryllopez/sharpeye.ai/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=arryllopez/sharpeye.ai" alt="contrib.rocks image" />
</a>



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Arryl Lopez - [@arryllopez](https://twitter.com/arryllopez) - arryllopez@gmail.com

Project Link: [https://github.com/arryllopez/sharpeye.ai](https://github.com/arryllopez/sharpeye.ai)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [TheOdds API](https://the-odds-api.com)
* [FastAPI](https://fastapi.tiangolo.com)
* [XGBoost Documentation](https://xgboost.readthedocs.io)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/arryllopez/sharpeye.ai.svg?style=for-the-badge
[contributors-url]: https://github.com/arryllopez/sharpeye.ai/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/arryllopez/sharpeye.ai.svg?style=for-the-badge
[forks-url]: https://github.com/arryllopez/sharpeye.ai/network/members
[stars-shield]: https://img.shields.io/github/stars/arryllopez/sharpeye.ai.svg?style=for-the-badge
[stars-url]: https://github.com/arryllopez/sharpeye.ai/stargazers
[issues-shield]: https://img.shields.io/github/issues/arryllopez/sharpeye.ai.svg?style=for-the-badge
[issues-url]: https://github.com/arryllopez/sharpeye.ai/issues
[license-shield]: https://img.shields.io/github/license/arryllopez/sharpeye.ai.svg?style=for-the-badge
[license-url]: https://github.com/arryllopez/sharpeye.ai/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/arryllopez
[product-screenshot]: images/screenshot.png
<!-- Shields.io badges. You can a comprehensive list with many more badges at: https://github.com/inttter/md-badges -->

[FastAPI]: https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white
[FastAPI-url]: https://fastapi.tiangolo.com/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[PostgreSQL]: https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white
[PostgreSQL-url]: https://www.postgresql.org/
[Python]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[Railway]: https://img.shields.io/badge/Railway-131415?style=for-the-badge&logo=railway&logoColor=white
[Railway-url]: https://railway.app/
[Vercel]: https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white
[Vercel-url]: https://vercel.com/
[AWS]: https://img.shields.io/badge/AWS_Lambda-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white
[AWS-url]: https://aws.amazon.com/lambda/
[Pandas]: https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white
[Pandas-url]: https://pandas.pydata.org/
