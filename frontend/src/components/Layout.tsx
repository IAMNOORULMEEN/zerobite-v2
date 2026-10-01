import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import type { Role } from "../types/auth";
import styles from "./Layout.module.scss";

interface NavItem {
  to: string;
  label: string;
  roles?: Role[];
}

const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Home" },
  { to: "/profile", label: "Profile" },
  { to: "/admin/ngos", label: "NGO review", roles: ["ADMIN"] },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const visibleItems = NAV_ITEMS.filter(
    (item) => !item.roles || (user && item.roles.includes(user.role)),
  );

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <div className={styles.bar}>
          <NavLink to="/" className={styles.brand} aria-label="ZeroBite home">
            ZeroBite
          </NavLink>

          <nav className={styles.nav} aria-label="Primary">
            <ul className={styles.navList}>
              {visibleItems.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.to === "/"}
                    className={({ isActive }) =>
                      isActive ? `${styles.link} ${styles.linkActive}` : styles.link
                    }
                  >
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>

          <div className={styles.account}>
            {user ? (
              <>
                <span className={styles.who} title={user.email}>
                  {user.full_name || user.email}
                </span>
                <button
                  type="button"
                  className={styles.logout}
                  onClick={handleLogout}
                >
                  Log out
                </button>
              </>
            ) : (
              <NavLink to="/login" className={styles.link}>
                Log in
              </NavLink>
            )}
          </div>
        </div>
      </header>

      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}
