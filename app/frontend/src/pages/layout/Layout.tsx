import { Outlet, NavLink, Link } from "react-router-dom";

import github from "../../assets/github.svg"

import styles from "./Layout.module.css";

const Layout = () => {
    return (
        <div className={styles.layout}>
            <header className={styles.header} role={"banner"}>
                <div className={styles.headerContainer}>
                    <Link to="https://dataaipdfchat.azurewebsites.net/" target={"_blank"} className={styles.headerTitleContainer}>
                        <h3 className={styles.headerTitle}>Chat and Ask</h3>
                    </Link>
                    <nav>
                        <ul className={styles.headerNavList}>
                            <li className={styles.headerNavLeftMargin}>
                                <NavLink to="/upload" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                Upload &nbsp;&nbsp;&nbsp;
                                </NavLink>
                            </li>
                            {/* <li>
                                <NavLink to="/botchat" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}> 
                                    Bot Chat&nbsp;&nbsp;
                                </NavLink>
                            </li> */}
                            {/* <li>
                                <NavLink to="/chat" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}> 
                                    Chat Stream&nbsp;&nbsp;
                                </NavLink>
                            </li> */}
                            <li>
                                <NavLink to="/" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                    Chat
                                </NavLink>
                            </li>
                            <li className={styles.headerNavLeftMargin}>
                                <NavLink to="/qa" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                    Ask a question
                                </NavLink>
                            </li>
                            <li className={styles.headerNavLeftMargin}>
                                <NavLink to="/sql" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                    Sql NLP
                                </NavLink>
                            </li>
                            <li className={styles.headerNavLeftMargin}>
                                <NavLink to="/speech" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                    Speech Analytics
                                </NavLink>
                            </li>
                            <li className={styles.headerNavLeftMargin}>
                                <NavLink to="/edgar" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                    Edgar Analysis
                                </NavLink>
                            </li>
                            {/* <li className={styles.headerNavLeftMargin}>
                                <NavLink to="/help" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                    Help
                                </NavLink>
                            </li> */}
                            <li className={styles.headerNavLeftMargin}>
                                <a href="https://github.com/akshata29/chatpdf" target={"_blank"} title="Github repository link">
                                    <img
                                        src={github}
                                        alt="Github logo"
                                        aria-label="Link to github repository"
                                        width="20px"
                                        height="20px"
                                        className={styles.githubLogo}
                                    />
                                </a>
                            </li>
                        </ul>
                    </nav>
                    <h4 className={styles.headerRightText}>Azure OpenAI</h4>
                </div>
            </header>

            <Outlet />
        </div>
    );
};

export default Layout;
