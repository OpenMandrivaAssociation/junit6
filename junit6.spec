Name:		junit6
Version:	6.0.3
Release:	1
Summary:	JUnit Platform 6 launcher, engine, and commons
Group:		Development/Java
License:	EPL-2.0
URL:		https://junit.org/junit5/
Source0:	junit-framework-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem
BuildRequires:	mvn(org.apiguardian:apiguardian-api)
BuildRequires:	apiguardian >= 1.1.2
BuildRequires:	mvn(org.jspecify:jspecify)
BuildRequires:	jspecify >= 1.0.0
BuildRequires:	mvn(org.opentest4j:opentest4j)
BuildRequires:	opentest4j >= 1.3.0
BuildRequires:	mvn(org.jetbrains.kotlin:kotlin-stdlib)
BuildRequires:	mvn(org.jetbrains.kotlin:kotlin-reflect)
BuildRequires:	mvn(org.jetbrains.kotlinx:kotlinx-coroutines-core-jvm)
BuildRequires:	kotlin-libs

%description
JUnit Platform %{version} commons, engine, and launcher. Gradle 9.9.1
asks the build for junit-platform-launcher %{version}. JUnit 5 is a
different major and keeps the unversioned indexes. These three jars are
versioned side artifacts. The suspending-function helper is Java that
imports the system Kotlin libraries.

%prep
%autosetup -n junit-framework-r%{version} -p1
find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > binaries.list
find . -type d -name '*.jar' -print >> binaries.list
if [ -s binaries.list ]; then
	cat binaries.list
	exit 1
fi

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
CP="%{_javadir}/apiguardian-api.jar:%{_javadir}/jspecify.jar:%{_javadir}/opentest4j/opentest4j.jar:%{_javadir}/kotlin-stdlib.jar:%{_javadir}/kotlin-reflect.jar:%{_javadir}/kotlinx-coroutines-core-jvm.jar"
for jar in apiguardian-api.jar jspecify.jar opentest4j/opentest4j.jar kotlin-stdlib.jar kotlin-reflect.jar kotlinx-coroutines-core-jvm.jar; do
	test -s "%{_javadir}/$jar"
done

compile_mod() {
	mod=$1
	extra=$2
	modulename=$3
	mkdir -p "classes/$mod"
	find "$mod/src/main/java" -name '*.java' ! -name 'module-info.java' > "$mod.list"
	test -s "$mod.list"
	javac --release 17 -encoding UTF-8 -Xlint:-options,-removal -proc:none \
		-cp "$CP:$extra" -d "classes/$mod" @"$mod.list"
	if [ -d "$mod/src/main/resources" ]; then
		cp -a "$mod/src/main/resources/." "classes/$mod/"
	fi
	echo "Automatic-Module-Name: $modulename" > "$mod.mf"
	jar cfm "$mod.jar" "$mod.mf" -C "classes/$mod" .
	jar i "$mod.jar"
}

compile_mod junit-platform-commons "" org.junit.platform.commons
compile_mod junit-platform-engine classes/junit-platform-commons org.junit.platform.engine
compile_mod junit-platform-launcher "classes/junit-platform-commons:classes/junit-platform-engine" org.junit.platform.launcher

test "$(wc -l < junit-platform-commons.list)" -eq 67
test "$(wc -l < junit-platform-engine.list)" -eq 110
test "$(wc -l < junit-platform-launcher.list)" -eq 98
javap -v -classpath junit-platform-launcher.jar org.junit.platform.launcher.core.LauncherFactory | grep -F -q 'major version: 61'
desc=$(jar --describe-module --file junit-platform-launcher.jar)
printf '%s\n' "$desc" | grep -F -q 'org.junit.platform.launcher'
if printf '%s\n' "$desc" | grep -F -q 'Unable'; then
	exit 1
fi

write_pom() {
	mod=$1
	deps=$2
	cat > "$mod.pom" <<END
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.junit.platform</groupId>
  <artifactId>$mod</artifactId>
  <version>%{version}</version>
  <name>$mod</name>
  <description>JUnit Platform $mod %{version}.</description>
  <url>https://junit.org/junit5/</url>
  <licenses>
    <license>
      <name>EPL-2.0</name>
      <url>https://www.eclipse.org/legal/epl-2.0/</url>
      <distribution>repo</distribution>
    </license>
  </licenses>
$deps
</project>
END
}
write_pom junit-platform-commons '  <dependencies>
    <dependency>
      <groupId>org.apiguardian</groupId>
      <artifactId>apiguardian-api</artifactId>
      <version>1.1.2</version>
      <optional>true</optional>
    </dependency>
    <dependency>
      <groupId>org.jspecify</groupId>
      <artifactId>jspecify</artifactId>
      <version>1.0.0</version>
      <optional>true</optional>
    </dependency>
  </dependencies>'
write_pom junit-platform-engine '  <dependencies>
    <dependency>
      <groupId>org.junit.platform</groupId>
      <artifactId>junit-platform-commons</artifactId>
      <version>%{version}</version>
    </dependency>
    <dependency>
      <groupId>org.opentest4j</groupId>
      <artifactId>opentest4j</artifactId>
      <version>1.3.0</version>
    </dependency>
    <dependency>
      <groupId>org.apiguardian</groupId>
      <artifactId>apiguardian-api</artifactId>
      <version>1.1.2</version>
      <optional>true</optional>
    </dependency>
    <dependency>
      <groupId>org.jspecify</groupId>
      <artifactId>jspecify</artifactId>
      <version>1.0.0</version>
      <optional>true</optional>
    </dependency>
  </dependencies>'
write_pom junit-platform-launcher '  <dependencies>
    <dependency>
      <groupId>org.junit.platform</groupId>
      <artifactId>junit-platform-commons</artifactId>
      <version>%{version}</version>
    </dependency>
    <dependency>
      <groupId>org.junit.platform</groupId>
      <artifactId>junit-platform-engine</artifactId>
      <version>%{version}</version>
    </dependency>
    <dependency>
      <groupId>org.apiguardian</groupId>
      <artifactId>apiguardian-api</artifactId>
      <version>1.1.2</version>
      <optional>true</optional>
    </dependency>
    <dependency>
      <groupId>org.jspecify</groupId>
      <artifactId>jspecify</artifactId>
      <version>1.0.0</version>
      <optional>true</optional>
    </dependency>
  </dependencies>'

%install
set -eo pipefail
: > .mfiles
pin_side() {
	mod=$1
	sysjar install --buildroot %{buildroot} \
		--artifact "$mod.pom:$mod.jar" \
		--file-name "$mod-%{version}" \
		--filelist ".mfiles-$mod"
	index="%{buildroot}/usr/share/sysjar/index/org.junit.platform/${mod}.sysjar"
	test -f "$index"
	/bin/mv "$index" "%{buildroot}/usr/share/sysjar/index/org.junit.platform/${mod}-%{version}.sysjar"
	sed -i "s|/usr/share/sysjar/index/org.junit.platform/${mod}\\.sysjar|/usr/share/sysjar/index/org.junit.platform/${mod}-%{version}.sysjar|" ".mfiles-$mod"
	grep -F -q '"version": "%{version}"' "%{buildroot}/usr/share/sysjar/index/org.junit.platform/${mod}-%{version}.sysjar"
	while IFS= read -r line; do
		grep -qxF -- "$line" .mfiles || printf '%s\n' "$line" >> .mfiles
	done < ".mfiles-$mod"
}
pin_side junit-platform-commons
pin_side junit-platform-engine
pin_side junit-platform-launcher
grep -F -q 'junit-platform-launcher-%{version}.jar' .mfiles
if grep -E -q '/junit-platform-(commons|engine|launcher)\.sysjar$' .mfiles; then
	exit 1
fi

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
mkdir -p check
cat > check/Smoke.java <<'END'
import org.junit.platform.engine.UniqueId;
import org.junit.platform.launcher.Launcher;
import org.junit.platform.launcher.core.LauncherFactory;

public class Smoke {
	public static void main(String[] args) {
		UniqueId id = UniqueId.forEngine("smoke");
		Launcher launcher = LauncherFactory.create();
		System.out.println(args[0] + " " + id.getEngineId().orElse("none") + " " + launcher.getClass().getSimpleName() + " %{version}");
	}
}
END
CP="%{buildroot}%{_javadir}/junit-platform-commons-%{version}.jar:%{buildroot}%{_javadir}/junit-platform-engine-%{version}.jar:%{buildroot}%{_javadir}/junit-platform-launcher-%{version}.jar:%{_javadir}/opentest4j/opentest4j.jar"
javac --release 17 -encoding UTF-8 -proc:none -cp "$CP" -d check check/Smoke.java
java -cp "check:$CP" Smoke junit603_ok > check.log
cat check.log
grep -F -q 'junit603_ok smoke SessionPerRequestLauncher %{version}' check.log

%files -f .mfiles
%doc README.md
%license LICENSE.md
