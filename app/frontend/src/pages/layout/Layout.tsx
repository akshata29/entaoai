import { useRef, useState, useEffect } from "react";
import { Outlet, NavLink, Link } from "react-router-dom";
import { Checkbox, ChoiceGroup, IChoiceGroupOption, Panel, DefaultButton, Spinner, TextField, SpinButton, Stack, IPivotItemProps, getFadedOverflowStyle} from "@fluentui/react";

import github from "../../assets/github.svg"

import styles from "./Layout.module.css";
import { SettingsButton } from "../../components/SettingsButton/SettingsButton";


const Layout = () => {
    const [isConfigPanelOpen, setIsConfigPanelOpen] = useState(false);
    const [showUpload, setShowUpload] = useState<boolean>(false);
    const [showEdgar, setshowEdgar] = useState<boolean>(false);
    const [showAdmin, setShowAdmin] = useState<boolean>(false);
    const [showSpeech, setShowSpeech] = useState<boolean>(true);

    const onShowUpload = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setShowUpload(!!checked);
    };

    const onShowAdmin = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setShowAdmin(!!checked);
    };

    const onShowEdgar = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setshowEdgar(!!checked);
    };

    const onShowSpeech = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setShowSpeech(!!checked);
    };

    return (
        <div className={styles.layout}>
            <header className={styles.header} role={"banner"}>
                <div className={styles.headerContainer}>
                    <Link to="https://dataaipdfchat.azurewebsites.net/" target={"_blank"} className={styles.headerTitleContainer}>
                        <h3 className={styles.headerTitle}>Chat and Ask</h3>
                    </Link>
                    <nav>
                        <ul className={styles.headerNavList}>
                            {showUpload && (
                                <li className={styles.headerNavLeftMargin}>
                                    <NavLink to="/upload" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                    Upload &nbsp;&nbsp;&nbsp;
                                    </NavLink>
                                </li>
                            )}
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
                                <NavLink to="/summary" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                    Summarization
                                </NavLink>
                            </li>
                            <li className={styles.headerNavLeftMargin}>
                                <NavLink to="/sql" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                    Sql NLP
                                </NavLink>
                            </li>
                            <li className={styles.headerNavLeftMargin}>
                                <NavLink to="/smartagent" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                    Smart Agent
                                </NavLink>
                            </li>
                            <li className={styles.headerNavLeftMargin}>
                                <NavLink to="/developer" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                    Developer Tools
                                </NavLink>
                            </li>
                            { showSpeech && (
                                <li className={styles.headerNavLeftMargin}>
                                    <NavLink to="/speech" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                        Speech Analytics
                                    </NavLink>
                                 </li>
                            )}
                            {showEdgar && (
                                 <li className={styles.headerNavLeftMargin}>
                                 <NavLink to="/edgar" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                     Edgar Analysis
                                 </NavLink>
                             </li>
                            )}
                            {showAdmin && (
                                 <li className={styles.headerNavLeftMargin}>
                                 <NavLink to="/admin" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                     Admin
                                 </NavLink>
                             </li>
                            )}
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
                            <li className={styles.headerNavLeftMargin}>
                                <SettingsButton className={styles.settingsButton} onClick={() => setIsConfigPanelOpen(!isConfigPanelOpen)} />
                            </li>
                        </ul>
                    </nav>
                    <h4 className={styles.headerRightText}>Azure OpenAI</h4>
                </div>
            </header>
            <Panel
                headerText="Configure Page Settings"
                isOpen={isConfigPanelOpen}
                isBlocking={false}
                onDismiss={() => setIsConfigPanelOpen(false)}
                closeButtonAriaLabel="Close"
                onRenderFooterContent={() => <DefaultButton onClick={() => setIsConfigPanelOpen(false)}>Close</DefaultButton>}
                isFooterAtBottom={true}
            >
                <br/>
                <Checkbox
                    className={styles.chatSettingsSeparator}
                    checked={showUpload}
                    label="Show Upload Capability"
                    onChange={onShowUpload}
                />
                <br/>
                <Checkbox
                    className={styles.chatSettingsSeparator}
                    checked={showEdgar}
                    label="Display Edgar Analysis"
                    onChange={onShowEdgar}
                />
                <br/>
                <Checkbox
                    className={styles.chatSettingsSeparator}
                    checked={showSpeech}
                    label="Display Speech Analytics"
                    onChange={onShowSpeech}
                />
                <br/>
                <Checkbox
                    className={styles.chatSettingsSeparator}
                    checked={showAdmin}
                    label="Display Admin Features"
                    onChange={onShowAdmin}
                />
            </Panel>
            <Outlet />
        </div>
    );
};

export default Layout;
