import { LeftNavigationSidebar } from "../../../components/LeftNavigationSidebar";
import { TopHeaderStatsBar } from "../../../components/TopHeaderStatsBar";
import { ProjectsGridCards } from "../../../components/ProjectsGridCards";
import { AnalyticsSidebarPanels } from "../../../components/AnalyticsSidebarPanels";

/**
 * COX page slug: dashboard
 * Page type: dashboard_overview
 * Visible regions: left_navigation_sidebar, top_header_stats_bar, projects_grid_cards, analytics_sidebar_panels
 * Desktop layout: App shell with left navigation, top header/stats bar, central projects grid, optional right analytics rail.
 * Tablet layout: Collapse analytics rail below main content or into tabbed panel.
 * Mobile layout: Stack header, filters, project cards, and analytics sections vertically.
 */
export interface DashboardPageProps {}

export function DashboardPage(_: DashboardPageProps) {
  return (
    <main data-cox-page="dashboard">
      <LeftNavigationSidebar />
      <TopHeaderStatsBar />
      <ProjectsGridCards />
      <AnalyticsSidebarPanels />
    </main>
  );
}
