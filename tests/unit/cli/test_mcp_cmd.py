"""Tests for hckg install claude / status / remove / doctor."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from cli import install_cmd
from cli.main import cli

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_project_tree(tmpdir: str) -> Path:
    """Create a minimal project tree with src/mcp_server/server.py."""
    root = Path(tmpdir) / "project"
    (root / "src" / "mcp_server").mkdir(parents=True)
    (root / "src" / "mcp_server" / "server.py").write_text("# server\n")
    (root / "pyproject.toml").write_text('[project]\nname = "hc-enterprise-kg"\n')
    return root


def _make_config(tmpdir: str, entry: dict | None = None) -> Path:
    """Write a Claude Desktop config and return the path."""
    path = Path(tmpdir) / "claude_desktop_config.json"
    config: dict = {"mcpServers": {}}
    if entry is not None:
        config["mcpServers"]["hc-enterprise-kg"] = entry
    path.write_text(json.dumps(config))
    return path


def _valid_entry(python: str = sys.executable, cwd: str | None = None) -> dict:
    """Return a valid server entry dict."""
    e: dict = {"command": python, "args": ["-m", "mcp_server.server"]}
    if cwd:
        e["cwd"] = cwd
    return e


# ===================================================================
# _read_config / _write_config
# ===================================================================


class TestConfigIO:
    def test_read_missing_file(self, tmp_path: Path):
        assert install_cmd._read_config(tmp_path / "nope.json") == {}

    def test_read_empty_file(self, tmp_path: Path):
        p = tmp_path / "empty.json"
        p.write_text("")
        assert install_cmd._read_config(p) == {}

    def test_read_valid_json(self, tmp_path: Path):
        p = tmp_path / "ok.json"
        p.write_text('{"a": 1}')
        assert install_cmd._read_config(p) == {"a": 1}

    def test_read_malformed_json_exits(self, tmp_path: Path):
        p = tmp_path / "bad.json"
        p.write_text("{broken")
        with pytest.raises(SystemExit):
            install_cmd._read_config(p)

    def test_read_non_object_json_exits(self, tmp_path: Path):
        p = tmp_path / "arr.json"
        p.write_text("[1, 2, 3]")
        with pytest.raises(SystemExit):
            install_cmd._read_config(p)

    def test_write_creates_parent_dirs(self, tmp_path: Path):
        p = tmp_path / "sub" / "dir" / "config.json"
        install_cmd._write_config(p, {"hello": "world"})
        assert p.exists()
        assert json.loads(p.read_text()) == {"hello": "world"}

    def test_write_atomic_preserves_content(self, tmp_path: Path):
        p = tmp_path / "config.json"
        p.write_text('{"old": true}')
        install_cmd._write_config(p, {"new": True})
        assert json.loads(p.read_text()) == {"new": True}


# ===================================================================
# Detection helpers
# ===================================================================


class TestDetection:
    def test_detect_python_path_returns_executable(self):
        result = install_cmd._detect_python_path()
        assert result == sys.executable

    def test_detect_python_path_empty_raises(self):
        with patch.object(sys, "executable", ""), pytest.raises(Exception):  # noqa: B017
            install_cmd._detect_python_path()

    def test_is_source_checkout_from_repo(self):
        # Running tests from the repo, so this should be True
        assert install_cmd._is_source_checkout() is True

    def test_is_source_checkout_from_site_packages(self):
        with patch("cli.install_cmd.__file__", "/fake/site-packages/cli/install_cmd.py"):
            assert install_cmd._is_source_checkout() is False

    def test_detect_project_root_finds_repo(self):
        root = install_cmd._detect_project_root()
        assert root is not None
        assert (root / "pyproject.toml").exists()

    def test_detect_project_root_returns_none_for_pip_install(self):
        with patch("cli.install_cmd._is_source_checkout", return_value=False):
            assert install_cmd._detect_project_root() is None

    def test_detect_project_root_ignores_wrong_pyproject(self, tmp_path: Path):
        """A pyproject.toml that isn't hc-enterprise-kg is skipped."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "other-project"\n')
        fake_file = tmp_path / "cli" / "install_cmd.py"
        fake_file.parent.mkdir(parents=True)
        fake_file.write_text("")
        with (
            patch("cli.install_cmd.__file__", str(fake_file)),
            patch("cli.install_cmd._is_source_checkout", return_value=True),
        ):
            result = install_cmd._detect_project_root()
            # Should not match "other-project"
            if result is not None:
                text = (result / "pyproject.toml").read_text()
                assert "hc-enterprise-kg" in text

    def test_detect_claude_config_darwin(self):
        with patch("cli.install_cmd.platform.system", return_value="Darwin"):
            p = install_cmd._detect_claude_config_path()
            assert p is not None
            assert "Claude" in str(p)
            assert str(p).endswith("claude_desktop_config.json")

    def test_detect_claude_config_windows(self):
        with (
            patch("cli.install_cmd.platform.system", return_value="Windows"),
            patch.dict(os.environ, {"APPDATA": "/fake/AppData"}),
        ):
            p = install_cmd._detect_claude_config_path()
            assert p is not None
            assert "fake" in str(p)

    def test_detect_claude_config_linux(self):
        with (
            patch("cli.install_cmd.platform.system", return_value="Linux"),
            patch.dict(os.environ, {"XDG_CONFIG_HOME": "/fake/config"}),
        ):
            p = install_cmd._detect_claude_config_path()
            assert p is not None
            assert "fake" in str(p)

    def test_detect_claude_config_unknown_os(self):
        with patch("cli.install_cmd.platform.system", return_value="FreeBSD"):
            assert install_cmd._detect_claude_config_path() is None


# ===================================================================
# Pre-flight checks
# ===================================================================


class TestCheckPythonVersion:
    def test_current_python_passes(self):
        ok, detail = install_cmd._check_python_version(sys.executable)
        assert ok is True
        assert "Python" in detail

    def test_nonexistent_interpreter(self):
        ok, detail = install_cmd._check_python_version("/nonexistent/python")
        assert ok is False
        assert "not found" in detail

    def test_old_python_fails(self):
        fake = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="Python 3.9.7\n",
            stderr="",
        )
        with patch("cli.install_cmd.subprocess.run", return_value=fake):
            ok, detail = install_cmd._check_python_version(sys.executable)
            assert ok is False
            assert "3.11" in detail

    def test_unparseable_version(self):
        fake = subprocess.CompletedProcess(args=[], returncode=0, stdout="garbage\n", stderr="")
        with patch("cli.install_cmd.subprocess.run", return_value=fake):
            ok, detail = install_cmd._check_python_version(sys.executable)
            assert ok is False
            assert "could not parse" in detail

    def test_timeout(self):
        side_effect = subprocess.TimeoutExpired("cmd", 10)
        with patch("cli.install_cmd.subprocess.run", side_effect=side_effect):
            ok, detail = install_cmd._check_python_version(sys.executable)
            assert ok is False
            assert "timed out" in detail


class TestCheckMcpImportable:
    def test_current_env_passes(self):
        ok, detail = install_cmd._check_mcp_importable(sys.executable)
        assert ok is True

    def test_nonexistent_interpreter(self):
        ok, detail = install_cmd._check_mcp_importable("/nonexistent/python")
        assert ok is False
        assert "not found" in detail

    def test_missing_module_shows_fix(self):
        fake = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="ModuleNotFoundError: No module named 'mcp'",
        )
        with patch("cli.install_cmd.subprocess.run", return_value=fake):
            ok, detail = install_cmd._check_mcp_importable(sys.executable)
            assert ok is False
            assert "poetry install --extras mcp" in detail
            assert "pip install" in detail

    def test_other_import_error(self):
        fake = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="ImportError: cannot import name 'Foo'",
        )
        with patch("cli.install_cmd.subprocess.run", return_value=fake):
            ok, detail = install_cmd._check_mcp_importable(sys.executable)
            assert ok is False
            assert "import failed" in detail

    def test_timeout(self):
        side_effect = subprocess.TimeoutExpired("cmd", 15)
        with patch("cli.install_cmd.subprocess.run", side_effect=side_effect):
            ok, detail = install_cmd._check_mcp_importable(sys.executable)
            assert ok is False
            assert "timed out" in detail


class TestCheckServerImportable:
    def test_current_env_passes(self):
        ok, detail = install_cmd._check_server_importable(sys.executable)
        assert ok is True

    def test_nonexistent_interpreter(self):
        ok, detail = install_cmd._check_server_importable("/nonexistent/python")
        assert ok is False

    def test_missing_mcp_server_shows_fix(self):
        fake = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="ModuleNotFoundError: No module named 'mcp_server'",
        )
        with patch("cli.install_cmd.subprocess.run", return_value=fake):
            ok, detail = install_cmd._check_server_importable(sys.executable)
            assert ok is False
            assert "not installed" in detail
            assert "poetry install" in detail

    def test_missing_mcp_dependency_shows_fix(self):
        fake = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="ModuleNotFoundError: No module named 'mcp'",
        )
        with patch("cli.install_cmd.subprocess.run", return_value=fake):
            ok, detail = install_cmd._check_server_importable(sys.executable)
            assert ok is False
            assert "mcp" in detail


class TestRunPreflight:
    def test_all_pass(self):
        checks = install_cmd._run_preflight(sys.executable)
        assert len(checks) == 3
        assert all(passed for _, passed, _ in checks)

    def test_short_circuits_on_bad_python(self):
        checks = install_cmd._run_preflight("/nonexistent/python")
        assert len(checks) == 3
        assert checks[0][1] is False  # Python version
        assert "skipped" in checks[1][2]  # MCP SDK
        assert "skipped" in checks[2][2]  # Server module


class TestPrintChecks:
    def test_counts_failures(self):
        checks = [
            ("A", True, "ok"),
            ("B", False, "fail\n  Fix: something"),
            ("C", True, "ok"),
        ]
        assert install_cmd._print_checks(checks) == 1

    def test_all_pass(self):
        checks = [("A", True, "ok"), ("B", True, "ok")]
        assert install_cmd._print_checks(checks) == 0


# ===================================================================
# _build_server_entry
# ===================================================================


class TestBuildServerEntry:
    def test_with_source_checkout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = _setup_project_tree(tmpdir)
            entry = install_cmd._build_server_entry(sys.executable, root, None)
            assert entry["command"] == sys.executable
            assert entry["args"] == ["-m", "mcp_server.server"]
            assert entry["cwd"] == str(root / "src")

    def test_without_source_checkout(self):
        entry = install_cmd._build_server_entry(sys.executable, None, None)
        assert entry["command"] == sys.executable
        assert entry["args"] == ["-m", "mcp_server.server"]
        assert "cwd" not in entry

    def test_with_graph(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            graph = Path(tmpdir) / "graph.json"
            graph.write_text("{}")
            entry = install_cmd._build_server_entry(sys.executable, None, str(graph))
            assert "env" in entry
            assert "HCKG_DEFAULT_GRAPH" in entry["env"]

    def test_source_checkout_no_src_dir(self):
        """If project_root exists but has no src/, cwd is omitted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "project"
            root.mkdir()
            entry = install_cmd._build_server_entry(sys.executable, root, None)
            assert "cwd" not in entry


# ===================================================================
# sync_claude_graph_path
# ===================================================================


class TestSyncClaudeGraphPath:
    def test_updates_registered_config(self, tmp_path: Path):
        config_path = _make_config(str(tmp_path), _valid_entry())
        graph = tmp_path / "new_graph.json"
        graph.write_text("{}")
        with patch("cli.install_cmd._detect_claude_config_path", return_value=config_path):
            result = install_cmd.sync_claude_graph_path(graph)
        assert result is True
        config = json.loads(config_path.read_text())
        entry = config["mcpServers"]["hc-enterprise-kg"]
        assert entry["env"]["HCKG_DEFAULT_GRAPH"] == str(graph.resolve())

    def test_returns_false_when_not_registered(self, tmp_path: Path):
        config_path = _make_config(str(tmp_path))  # empty servers
        graph = tmp_path / "graph.json"
        graph.write_text("{}")
        with patch("cli.install_cmd._detect_claude_config_path", return_value=config_path):
            result = install_cmd.sync_claude_graph_path(graph)
        assert result is False

    def test_returns_false_when_config_missing(self, tmp_path: Path):
        config_path = tmp_path / "nonexistent.json"
        with patch("cli.install_cmd._detect_claude_config_path", return_value=config_path):
            result = install_cmd.sync_claude_graph_path(tmp_path / "graph.json")
        assert result is False

    def test_returns_false_when_config_path_none(self):
        with patch("cli.install_cmd._detect_claude_config_path", return_value=None):
            result = install_cmd.sync_claude_graph_path("/any/graph.json")
        assert result is False

    def test_updates_existing_env(self, tmp_path: Path):
        """When env already has HCKG_DEFAULT_GRAPH, it gets replaced."""
        entry = _valid_entry()
        entry["env"] = {"HCKG_DEFAULT_GRAPH": "/old/graph.json"}
        config_path = _make_config(str(tmp_path), entry)
        new_graph = tmp_path / "updated.json"
        new_graph.write_text("{}")
        with patch("cli.install_cmd._detect_claude_config_path", return_value=config_path):
            result = install_cmd.sync_claude_graph_path(new_graph)
        assert result is True
        config = json.loads(config_path.read_text())
        assert config["mcpServers"]["hc-enterprise-kg"]["env"]["HCKG_DEFAULT_GRAPH"] == str(
            new_graph.resolve()
        )

    def test_preserves_other_env_vars(self, tmp_path: Path):
        """Other env vars in the entry are not disturbed."""
        entry = _valid_entry()
        entry["env"] = {"OTHER_VAR": "keep_me", "HCKG_DEFAULT_GRAPH": "/old/path"}
        config_path = _make_config(str(tmp_path), entry)
        new_graph = tmp_path / "g.json"
        new_graph.write_text("{}")
        with patch("cli.install_cmd._detect_claude_config_path", return_value=config_path):
            install_cmd.sync_claude_graph_path(new_graph)
        config = json.loads(config_path.read_text())
        assert config["mcpServers"]["hc-enterprise-kg"]["env"]["OTHER_VAR"] == "keep_me"


# ===================================================================
# _detect_default_graph
# ===================================================================


class TestGenerateDefaultGraph:
    def test_generates_to_project_root(self, tmp_path: Path):
        result = install_cmd._generate_default_graph(tmp_path)
        graph_path = Path(result)
        assert graph_path.exists()
        assert graph_path.parent == tmp_path
        assert Path(graph_path).name == "graph.json"
        data = json.loads(graph_path.read_text())
        assert "entities" in data
        assert len(data["entities"]) > 0

    def test_generates_to_cwd_when_no_root(self, tmp_path: Path):
        with patch("cli.install_cmd.Path.cwd", return_value=tmp_path):
            result = install_cmd._generate_default_graph(None)
        graph_path = Path(result)
        assert graph_path.exists()
        assert graph_path.parent.resolve() == tmp_path.resolve()


class TestDetectDefaultGraph:
    def test_finds_graph_in_project_root(self, tmp_path: Path):
        graph = tmp_path / "graph.json"
        graph.write_text("{}")
        result = install_cmd._detect_default_graph(tmp_path)
        assert result == graph.resolve()

    def test_finds_graph_in_cwd(self, tmp_path: Path):
        graph = tmp_path / "graph.json"
        graph.write_text("{}")
        with patch("cli.install_cmd.Path.cwd", return_value=tmp_path):
            result = install_cmd._detect_default_graph(None)
        assert result == graph.resolve()

    def test_prefers_project_root_over_cwd(self, tmp_path: Path):
        root_dir = tmp_path / "project"
        root_dir.mkdir()
        root_graph = root_dir / "graph.json"
        root_graph.write_text('{"source": "root"}')
        cwd_dir = tmp_path / "other"
        cwd_dir.mkdir()
        cwd_graph = cwd_dir / "graph.json"
        cwd_graph.write_text('{"source": "cwd"}')
        with patch("cli.install_cmd.Path.cwd", return_value=cwd_dir):
            result = install_cmd._detect_default_graph(root_dir)
        assert result == root_graph.resolve()

    def test_returns_none_when_no_graph(self, tmp_path: Path):
        with patch("cli.install_cmd.Path.cwd", return_value=tmp_path):
            result = install_cmd._detect_default_graph(None)
        assert result is None

    def test_returns_none_with_project_root_but_no_graph(self, tmp_path: Path):
        root_dir = tmp_path / "project"
        root_dir.mkdir()
        with patch("cli.install_cmd.Path.cwd", return_value=tmp_path):
            result = install_cmd._detect_default_graph(root_dir)
        assert result is None

    def test_ignores_directories_named_graph_json(self, tmp_path: Path):
        """A directory named graph.json should not be detected."""
        (tmp_path / "graph.json").mkdir()
        with patch("cli.install_cmd.Path.cwd", return_value=tmp_path):
            result = install_cmd._detect_default_graph(tmp_path)
        assert result is None

    def test_deduplicates_when_root_equals_cwd(self, tmp_path: Path):
        """When project root IS the cwd, graph.json is checked once."""
        graph = tmp_path / "graph.json"
        graph.write_text("{}")
        with patch("cli.install_cmd.Path.cwd", return_value=tmp_path):
            result = install_cmd._detect_default_graph(tmp_path)
        assert result == graph.resolve()


# ===================================================================
# install claude
# ===================================================================


class TestInstallClaude:
    def test_creates_config(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        result = CliRunner().invoke(cli, ["install", "claude", "--config", str(config_path)])
        assert result.exit_code == 0, result.output
        assert config_path.exists()
        config = json.loads(config_path.read_text())
        assert "hc-enterprise-kg" in config["mcpServers"]
        server = config["mcpServers"]["hc-enterprise-kg"]
        assert server["command"] == sys.executable
        assert server["args"] == ["-m", "mcp_server.server"]

    def test_preserves_existing_servers(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        config_path.write_text(
            json.dumps({"mcpServers": {"other": {"command": "node", "args": ["s.js"]}}})
        )
        result = CliRunner().invoke(cli, ["install", "claude", "--config", str(config_path)])
        assert result.exit_code == 0, result.output
        config = json.loads(config_path.read_text())
        assert "other" in config["mcpServers"]
        assert "hc-enterprise-kg" in config["mcpServers"]

    def test_updates_existing_registration(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        CliRunner().invoke(cli, ["install", "claude", "--config", str(config_path)])
        result = CliRunner().invoke(cli, ["install", "claude", "--config", str(config_path)])
        assert result.exit_code == 0, result.output
        assert "Updating" in result.output

    def test_skip_checks_bypasses_validation(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        result = CliRunner().invoke(
            cli, ["install", "claude", "--config", str(config_path), "--skip-checks"]
        )
        assert result.exit_code == 0, result.output
        assert "Pre-flight" not in result.output

    def test_fails_on_preflight_failure(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        fake = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="ModuleNotFoundError: No module named 'mcp'",
        )
        with patch("cli.install_cmd.subprocess.run", return_value=fake):
            result = CliRunner().invoke(cli, ["install", "claude", "--config", str(config_path)])
            assert result.exit_code != 0
            assert "FAIL" in result.output
            assert not config_path.exists()  # config NOT written on failure

    def test_malformed_existing_config(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        config_path.write_text("{broken json")
        result = CliRunner().invoke(cli, ["install", "claude", "--config", str(config_path)])
        assert result.exit_code != 0
        assert "malformed" in result.output

    def test_graph_warning_on_missing_file(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        result = CliRunner().invoke(
            cli,
            [
                "install",
                "claude",
                "--config",
                str(config_path),
                "--graph",
                "/nonexistent/graph.json",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "Warning" in result.output
        assert "not found" in result.output

    def test_mcpservers_not_dict_gets_replaced(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"mcpServers": "invalid"}))
        result = CliRunner().invoke(cli, ["install", "claude", "--config", str(config_path)])
        assert result.exit_code == 0, result.output
        config = json.loads(config_path.read_text())
        assert isinstance(config["mcpServers"], dict)

    def test_pip_install_mode_omits_cwd(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        with patch("cli.install_cmd._detect_project_root", return_value=None):
            result = CliRunner().invoke(cli, ["install", "claude", "--config", str(config_path)])
            assert result.exit_code == 0, result.output
            config = json.loads(config_path.read_text())
            entry = config["mcpServers"]["hc-enterprise-kg"]
            assert "cwd" not in entry

    def test_auto_detects_graph_in_project_root(self, tmp_path: Path):
        """When --graph is omitted, auto-detects graph.json in project root."""
        config_path = tmp_path / "config.json"
        project_root = _setup_project_tree(str(tmp_path))
        graph = project_root / "graph.json"
        graph.write_text('{"entities": [], "relationships": []}')
        with patch("cli.install_cmd._detect_project_root", return_value=project_root):
            result = CliRunner().invoke(
                cli, ["install", "claude", "--config", str(config_path)]
            )
        assert result.exit_code == 0, result.output
        assert "auto-detected" in result.output
        config = json.loads(config_path.read_text())
        entry = config["mcpServers"]["hc-enterprise-kg"]
        assert "HCKG_DEFAULT_GRAPH" in entry.get("env", {})
        assert entry["env"]["HCKG_DEFAULT_GRAPH"] == str(graph.resolve())

    def test_generates_graph_when_none_exists(self, tmp_path: Path):
        """When no graph exists anywhere, install generates a default one."""
        config_path = tmp_path / "config.json"
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / "src").mkdir()
        with (
            patch("cli.install_cmd._detect_default_graph", return_value=None),
            patch("cli.install_cmd._detect_project_root", return_value=project_root),
        ):
            result = CliRunner().invoke(
                cli, ["install", "claude", "--config", str(config_path)]
            )
        assert result.exit_code == 0, result.output
        assert "generated" in result.output.lower()
        assert "Generating default graph" in result.output
        # Config must have HCKG_DEFAULT_GRAPH set
        config = json.loads(config_path.read_text())
        entry = config["mcpServers"]["hc-enterprise-kg"]
        assert "HCKG_DEFAULT_GRAPH" in entry.get("env", {})
        # The generated graph file must exist
        graph_file = Path(entry["env"]["HCKG_DEFAULT_GRAPH"])
        assert graph_file.exists()
        assert graph_file.stat().st_size > 0

    def test_generated_graph_is_valid_json(self, tmp_path: Path):
        """Auto-generated graph is valid JSON with entities and relationships."""
        config_path = tmp_path / "config.json"
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / "src").mkdir()
        with (
            patch("cli.install_cmd._detect_default_graph", return_value=None),
            patch("cli.install_cmd._detect_project_root", return_value=project_root),
        ):
            CliRunner().invoke(cli, ["install", "claude", "--config", str(config_path)])
        config = json.loads(config_path.read_text())
        graph_file = Path(config["mcpServers"]["hc-enterprise-kg"]["env"]["HCKG_DEFAULT_GRAPH"])
        data = json.loads(graph_file.read_text())
        assert "entities" in data
        assert "relationships" in data
        assert len(data["entities"]) > 0
        assert len(data["relationships"]) > 0

    def test_always_has_graph_in_next_steps(self, tmp_path: Path):
        """Next steps always shows 'Show me graph statistics' since graph is guaranteed."""
        config_path = tmp_path / "config.json"
        graph = tmp_path / "graph.json"
        graph.write_text("{}")
        result = CliRunner().invoke(
            cli,
            ["install", "claude", "--config", str(config_path), "--graph", str(graph)],
        )
        assert result.exit_code == 0, result.output
        assert "Show me graph statistics" in result.output


# ===================================================================
# install doctor
# ===================================================================


class TestInstallDoctor:
    def _run_doctor(self, config_path: Path) -> object:
        original = install_cmd._detect_claude_config_path
        try:
            install_cmd._detect_claude_config_path = lambda: config_path
            return CliRunner().invoke(cli, ["install", "doctor"])
        finally:
            install_cmd._detect_claude_config_path = original

    def test_all_pass(self, tmp_path: Path):
        root = _setup_project_tree(str(tmp_path))
        config_path = _make_config(str(tmp_path), _valid_entry(cwd=str(root / "src")))
        result = self._run_doctor(config_path)
        assert result.exit_code == 0, result.output
        assert "All checks passed" in result.output

    def test_missing_python(self, tmp_path: Path):
        config_path = _make_config(str(tmp_path), _valid_entry(python="/nonexistent/python"))
        result = self._run_doctor(config_path)
        assert result.exit_code != 0
        assert "not found" in result.output

    def test_wrong_args(self, tmp_path: Path):
        entry = {"command": sys.executable, "args": ["wrong"]}
        config_path = _make_config(str(tmp_path), entry)
        result = self._run_doctor(config_path)
        assert result.exit_code != 0
        assert "unexpected args" in result.output

    def test_missing_cwd_dir(self, tmp_path: Path):
        entry = _valid_entry(cwd="/nonexistent/path/src")
        config_path = _make_config(str(tmp_path), entry)
        result = self._run_doctor(config_path)
        assert result.exit_code != 0
        assert "not found" in result.output

    def test_no_cwd_is_fine(self, tmp_path: Path):
        """Config without cwd should pass if modules are importable."""
        entry = _valid_entry()  # no cwd
        config_path = _make_config(str(tmp_path), entry)
        result = self._run_doctor(config_path)
        assert result.exit_code == 0, result.output

    def test_not_registered(self, tmp_path: Path):
        config_path = _make_config(str(tmp_path))  # empty servers
        result = self._run_doctor(config_path)
        assert result.exit_code != 0
        assert "not registered" in result.output

    def test_config_file_missing(self, tmp_path: Path):
        config_path = tmp_path / "nope.json"
        result = self._run_doctor(config_path)
        assert result.exit_code != 0

    def test_malformed_config(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        config_path.write_text("{bad json")
        result = self._run_doctor(config_path)
        assert result.exit_code != 0
        assert "malformed" in result.output

    def test_missing_graph_file(self, tmp_path: Path):
        entry = _valid_entry()
        entry["env"] = {"HCKG_DEFAULT_GRAPH": "/nonexistent/graph.json"}
        config_path = _make_config(str(tmp_path), entry)
        result = self._run_doctor(config_path)
        assert result.exit_code != 0
        assert "Graph file" in result.output

    def test_invalid_entry_type(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"mcpServers": {"hc-enterprise-kg": "not-a-dict"}}))
        result = self._run_doctor(config_path)
        assert result.exit_code != 0
        assert "not a valid" in result.output

    def test_empty_command(self, tmp_path: Path):
        entry = {"command": "", "args": ["-m", "mcp_server.server"]}
        config_path = _make_config(str(tmp_path), entry)
        result = self._run_doctor(config_path)
        assert result.exit_code != 0
        assert "FAIL" in result.output


# ===================================================================
# install status
# ===================================================================


class TestInstallStatus:
    def test_registered(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        CliRunner().invoke(cli, ["install", "claude", "--config", str(config_path)])
        original = install_cmd._detect_claude_config_path
        try:
            install_cmd._detect_claude_config_path = lambda: config_path
            result = CliRunner().invoke(cli, ["install", "status"])
            assert result.exit_code == 0, result.output
            assert "Registered" in result.output
        finally:
            install_cmd._detect_claude_config_path = original

    def test_not_registered(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"mcpServers": {}}))
        original = install_cmd._detect_claude_config_path
        try:
            install_cmd._detect_claude_config_path = lambda: config_path
            result = CliRunner().invoke(cli, ["install", "status"])
            assert result.exit_code == 0
            assert "Not registered" in result.output
        finally:
            install_cmd._detect_claude_config_path = original

    def test_malformed_config(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        config_path.write_text("{bad")
        original = install_cmd._detect_claude_config_path
        try:
            install_cmd._detect_claude_config_path = lambda: config_path
            result = CliRunner().invoke(cli, ["install", "status"])
            assert result.exit_code != 0
        finally:
            install_cmd._detect_claude_config_path = original

    def test_mcpservers_not_dict(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"mcpServers": "bad"}))
        original = install_cmd._detect_claude_config_path
        try:
            install_cmd._detect_claude_config_path = lambda: config_path
            result = CliRunner().invoke(cli, ["install", "status"])
            assert "Not registered" in result.output
        finally:
            install_cmd._detect_claude_config_path = original


# ===================================================================
# install remove
# ===================================================================


class TestInstallRemove:
    def test_remove_claude(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        CliRunner().invoke(cli, ["install", "claude", "--config", str(config_path)])
        original = install_cmd._detect_claude_config_path
        try:
            install_cmd._detect_claude_config_path = lambda: config_path
            result = CliRunner().invoke(cli, ["install", "remove", "claude"])
            assert result.exit_code == 0, result.output
            assert "Removed" in result.output
            config = json.loads(config_path.read_text())
            assert "hc-enterprise-kg" not in config.get("mcpServers", {})
        finally:
            install_cmd._detect_claude_config_path = original

    def test_remove_not_registered(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"mcpServers": {}}))
        original = install_cmd._detect_claude_config_path
        try:
            install_cmd._detect_claude_config_path = lambda: config_path
            result = CliRunner().invoke(cli, ["install", "remove", "claude"])
            assert result.exit_code == 0
            assert "not registered" in result.output or "Nothing" in result.output
        finally:
            install_cmd._detect_claude_config_path = original

    def test_remove_preserves_other_servers(self, tmp_path: Path):
        config_path = tmp_path / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "other": {"command": "node"},
                        "hc-enterprise-kg": {
                            "command": sys.executable,
                            "args": ["-m", "mcp_server.server"],
                        },
                    }
                }
            )
        )
        original = install_cmd._detect_claude_config_path
        try:
            install_cmd._detect_claude_config_path = lambda: config_path
            result = CliRunner().invoke(cli, ["install", "remove", "claude"])
            assert result.exit_code == 0
            config = json.loads(config_path.read_text())
            assert "other" in config["mcpServers"]
            assert "hc-enterprise-kg" not in config["mcpServers"]
        finally:
            install_cmd._detect_claude_config_path = original
