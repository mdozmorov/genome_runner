from setuptools import setup
from setuptools.command.develop import develop as _develop
from setuptools.command.install import install as _install
import os
import subprocess



def scrip_installer(command_subclass):
    """A decorator for classes subclassing one of the setuptools commands.

    It modifies the run() method so that is runs scripts to install required packages.
    Only works in Ubuntu
    """
    orig_run = command_subclass.run

    def modified_run(self):
        # installs all prerequisites and GRTK
        grtk_install = """mkdir downloads\ncd downloads\nsudo apt-get -y install python-setuptools python-pip python-dev parallel r-base-core bedtools samtools tabix kyotocabinet-utils realpath python-cherrypy3 python-numpy python-scipy\nsudo apt-get -y upgrade gcc\nsudo pip install -U cython\nwget -N https://github.com/bedops/bedops/releases/download/v2.3.0/bedops_linux_x86_64-v2.3.0.tar.bz2\nsudo tar xjvf bedops_linux_x86_64-v2.3.0.tar.bz2 -C /usr/local/\nsudo wget -np -R -A "bedToBigBed" -A "bedGraphToBigWig" -A "bigWig*" -A "bigBed*" -N -e robots=off -r -P /usr/local/bin -nd "http://hgdownload.cse.ucsc.edu/admin/exe/linux.x86_64/"\nsudo wget -o /usr/local/bin/rowsToCols http://hgdownload.cse.ucsc.edu/admin/exe/linux.x86_64/rowsToCols\nsudo chmod a+x /usr/local/bin/*\ngit clone https://mdozmorov@bitbucket.org/wrenlab/grtk.git\ncd grtk\nsudo python setup.py install\ncd ../..\nsudo rm -r downloads"""
        subprocess.Popen(grtk_install,stdout=subprocess.PIPE,shell=True).wait()
        # Install the R packages required by grsnp
        r_packages_install = "sudo Rscript installer.R"
        subprocess.Popen(r_packages_install,stdout=subprocess.PIPE,shell=True).wait()

        orig_run(self)

    command_subclass.run = modified_run
    return command_subclass

@scrip_installer
class CustomInstallCommand(_install):
    pass

@scrip_installer
class CustomDevelopCommand(_develop):
    pass

setup(
    name='GenomeRunner Web',
    version='0.1.0',
    author='Mikhail G. Dozmorov, Lukas R. Cara, Cory B. Giles',
    author_email='mikhail.dozmorov@gmail.com, lks_cara@yahoo.com, mail@corygil.es',
    data_files=[('grsnp', ['grsnp_db_readme.txt']),],
    packages=['grsnp'],
    package_dir={"grsnp": "grsnp"},
    #include_package_data= True,
    package_data={"grsnp": [
    "frontend/static/css/jquery.ui.core.js",
    "frontend/static/css/jquery.ui.fileinput.css",
    "frontend/static/css/jquery.checkboxtree.css",
    "frontend/static/css/demo_page.css",
    "frontend/static/css/bootstrap-responsive.css",
    "frontend/static/css/jquery.ui.menubar.css",
    "frontend/static/css/jquery.tipsy.css",
    "frontend/static/css/demo_table_jui.css",
    "frontend/static/css/__init__.py",
    "frontend/static/css/jquery.dataTables.css",
    "frontend/static/css/'",
    "frontend/static/css/bootstrap.min.css",
    "frontend/static/css/fonts/iconic_stroke.woff",
    "frontend/static/css/fonts/iconic_stroke.ttf",
    "frontend/static/css/fonts/iconic_stroke.svg",
    "frontend/static/css/fonts/iconic_stroke.eot",
    "frontend/static/css/fonts/__init__.py",
    "frontend/static/css/close.gif",
    "frontend/static/css/jquery.dataTables_themeroller.css",
    "frontend/static/css/main.css",
    "frontend/static/css/loading.gif",
    "frontend/static/css/TableTools_JUI.css",
    "frontend/static/css/demo_table.css",
    "frontend/static/css/smoothness/jquery-ui.css",
    "frontend/static/css/smoothness/__init__.py",
    "frontend/static/css/smoothness/images/ui-bg_glass_75_e6e6e6_1x400.png",
    "frontend/static/css/smoothness/images/ui-icons_454545_256x240.png",
    "frontend/static/css/smoothness/images/ui-bg_flat_75_ffffff_40x100.png",
    "frontend/static/css/smoothness/images/ui-icons_cd0a0a_256x240.png",
    "frontend/static/css/smoothness/images/ui-bg_flat_0_aaaaaa_40x100.png",
    "frontend/static/css/smoothness/images/ui-bg_glass_65_ffffff_1x400.png",
    "frontend/static/css/smoothness/images/ui-bg_highlight-soft_75_cccccc_1x100.png",
    "frontend/static/css/smoothness/images/ui-icons_2e83ff_256x240.png",
    "frontend/static/css/smoothness/images/ui-bg_glass_75_dadada_1x400.png",
    "frontend/static/css/smoothness/images/ui-icons_888888_256x240.png",
    "frontend/static/css/smoothness/images/ui-bg_glass_55_fbf9ee_1x400.png",
    "frontend/static/css/smoothness/images/ui-bg_glass_95_fef1ec_1x400.png",
    "frontend/static/css/smoothness/images/ui-icons_222222_256x240.png",
    "frontend/static/css/jquery.ui.menu.css",
    "frontend/static/css/TableTools.css",
    "frontend/static/css/ui-lightness/__init__.py",
    "frontend/static/css/ui-lightness/images/ui-bg_glass_75_e6e6e6_1x400.png",
    "frontend/static/css/ui-lightness/images/ui-icons_454545_256x240.png",
    "frontend/static/css/ui-lightness/images/ui-icons_cd0a0a_256x240.png",
    "frontend/static/css/ui-lightness/images/ui-bg_glass_75_ffffff_1x400.png",
    "frontend/static/css/ui-lightness/images/ui-bg_flat_0_aaaaaa_40x100.png",
    "frontend/static/css/ui-lightness/images/__init__.py",
    "frontend/static/css/ui-lightness/images/ui-bg_glass_65_ffffff_1x400.png",
    "frontend/static/css/ui-lightness/images/ui-bg_highlight-soft_75_cccccc_1x100.png",
    "frontend/static/css/ui-lightness/images/ui-icons_2e83ff_256x240.png",
    "frontend/static/css/ui-lightness/images/ui-bg_glass_75_dadada_1x400.png",
    "frontend/static/css/ui-lightness/images/ui-icons_888888_256x240.png",
    "frontend/static/css/ui-lightness/images/ui-bg_glass_55_fbf9ee_1x400.png",
    "frontend/static/css/ui-lightness/images/ui-icons_222222_256x240.png",
    "frontend/static/css/ui-lightness/images/ui-bg_inset-soft_95_fef1ec_1x100.png",
    "frontend/static/css/ui-lightness/images/ui-icons_f6cf3b_256x240.png",
    "frontend/static/css/ui-lightness/jquery.ui.1.8.16.ie.css",
    "frontend/static/css/ui-lightness/jquery-ui-1.8.16.custom.css",
    "frontend/static/css/combobox.css",
    "frontend/static/style.css",
    "frontend/static/__init__.py",
    "frontend/static/new-icon.jpg",
    "frontend/static/TableTools-2.1.2.zip",
    "frontend/static/gf_test.txt",
    "frontend/static/js/jquery.ui.core.js",
    "frontend/static/js/jquery.ui.widget.js",
    "frontend/static/js/jquery.dataTables_old.js",
    "frontend/static/js/bootstrap-modal.js",
    "frontend/static/js/jquery.slimScroll.min.js",
    "frontend/static/js/jquery.slimScroll.js",
    "frontend/static/js/bootstrap-popover.js",
    "frontend/static/js/fuse.js",
    "frontend/static/js/TableTools.min.js",
    "frontend/static/js/jquery.js",
    "frontend/static/js/bootstrap-scrollspy.js",
    "frontend/static/js/d3.js",
    "frontend/static/js/ZeroClipboard.js",
    "frontend/static/js/bootstrap-tabs.js",
    "frontend/static/js/bootstrap-dropdown.js",
    "frontend/static/js/bootstrap.min.js",
    "frontend/static/js/jquery.sly.min.js",
    "frontend/static/js/__init__.py",
    "frontend/static/js/jquery.ui.menu.js",
    "frontend/static/js/jquery.tipsy.js",
    "frontend/static/js/jquery-ui.js",
    "frontend/static/js/jquery-ui-1.8.22.custom.min.js",
    "frontend/static/js/jquery-1.7.2.min.js",
    "frontend/static/js/bootstrap-twipsy.js",
    "frontend/static/js/enhance.min.js",
    "frontend/static/js/jquery.ui.position.js",
    "frontend/static/js/fcbkcomplete.js",
    "frontend/static/js/jquery.dataTables.js",
    "frontend/static/js/jquery-1.4.4.js",
    "frontend/static/js/backbone.js",
    "frontend/static/js/fcbkcomplete.min.js",
    "frontend/static/js/d3.heatmap.js",
    "frontend/static/js/bootstrap-buttons.js",
    "frontend/static/js/jquery.fileinput.js",
    "frontend/static/js/bootstrap.js",
    "frontend/static/js/jquery.ui.menubar.js",
    "frontend/static/js/underscore.js",
    "frontend/static/js/jquery.checkboxtree.js",
    "frontend/static/js/bootstrap-alerts.js",
    "frontend/static/js/jquery.easytabs.min.js",
    "frontend/static/js/jquery.dataTables.min.js",
    "frontend/static/js/TableTools.js",
    "frontend/static/js/jquery.ui.button.js",
    "frontend/static/js/bootstrap-tooltip.js",
    "frontend/static/json.php",
    "frontend/static/images/plus.png",
    "frontend/static/images/logo-reversed-small.jpg",
    "frontend/static/images/forward_enabled_hover.png",
    "frontend/static/images/ui-bg_glass_75_e6e6e6_1x400.png",
    "frontend/static/images/favicon.ico",
    "frontend/static/images/ui-icons_454545_256x240.png",
    "frontend/static/images/rightArrow.gif",
    "frontend/static/images/glyphicons-halflings-white.png",
    "frontend/static/images/collection.png",
    "frontend/static/images/print.png",
    "frontend/static/images/downArrow.gif",
    "frontend/static/images/sort_desc_disabled.png",
    "frontend/static/images/sort_both.png",
    "frontend/static/images/ui-bg_flat_75_ffffff_40x100.png",
    "frontend/static/images/GROverview.png",
    "frontend/static/images/ui-icons_cd0a0a_256x240.png",
    "frontend/static/images/icon-image.gif",
    "frontend/static/images/collection_hover.png",
    "frontend/static/images/glyphicons-halflings.png",
    "frontend/static/images/ui-bg_flat_0_aaaaaa_40x100.png",
    "frontend/static/images/__init__.py",
    "frontend/static/images/icon-media.gif",
    "frontend/static/images/back_enabled.png",
    "frontend/static/images/ui-bg_glass_65_ffffff_1x400.png",
    "frontend/static/images/print_hover.png",
    "frontend/static/images/e-mail.png",
    "frontend/static/images/ui-bg_highlight-soft_75_cccccc_1x100.png",
    "frontend/static/images/coming_soon.png",
    "frontend/static/images/csv_hover.png",
    "frontend/static/images/ui-icons_2e83ff_256x240.png",
    "frontend/static/images/ui-bg_glass_75_dadada_1x400.png",
    "frontend/static/images/blank.png",
    "frontend/static/images/sort_asc.png",
    "frontend/static/images/Sorting icons.psd",
    "frontend/static/images/background.png",
    "frontend/static/images/GRLogo.gif",
    "frontend/static/images/copy.png",
    "frontend/static/images/forward_enabled.png",
    "frontend/static/images/ui-icons_888888_256x240.png",
    "frontend/static/images/back_enabled_hover.png",
    "frontend/static/images/minus.png",
    "frontend/static/images/ui-bg_glass_55_fbf9ee_1x400.png",
    "frontend/static/images/sort_asc_disabled.png",
    "frontend/static/images/icon-generic.gif",
    "frontend/static/images/back_disabled.png",
    "frontend/static/images/ui-bg_glass_95_fef1ec_1x400.png",
    "frontend/static/images/pdf.png",
    "frontend/static/images/ui-icons_222222_256x240.png",
    "frontend/static/images/forward_disabled.png",
    "frontend/static/images/pdf_hover.png",
    "frontend/static/images/copy_hover.png",
    "frontend/static/images/GRLogo.png",
    "frontend/static/images/xls.png",
    "frontend/static/images/help-icon.png",
    "frontend/static/images/icon-zip.gif",
    "frontend/static/images/xls_hover.png",
    "frontend/static/images/sort_desc.png",
    "frontend/static/images/csv.png",
    "frontend/static/close.gif",
    "frontend/static/loading.gif",
    "frontend/static/fetched.php",
    "frontend/static/gfs.php",
    "frontend/static/fetched.txt",
    "frontend/static/TableTools-2.1.2/button_text.html",
    "frontend/static/TableTools-2.1.2/media/css/__init__.py",
    "frontend/static/TableTools-2.1.2/media/css/TableTools_JUI.css",
    "frontend/static/TableTools-2.1.2/media/css/TableTools.css",
    "frontend/static/TableTools-2.1.2/media/__init__.py",
    "frontend/static/TableTools-2.1.2/media/js/TableTools.min.js",
    "frontend/static/TableTools-2.1.2/media/js/ZeroClipboard.js",
    "frontend/static/TableTools-2.1.2/media/js/__init__.py",
    "frontend/static/TableTools-2.1.2/media/js/TableTools.js",
    "frontend/static/TableTools-2.1.2/media/images/collection.png",
    "frontend/static/TableTools-2.1.2/media/images/print.png",
    "frontend/static/TableTools-2.1.2/media/images/collection_hover.png",
    "frontend/static/TableTools-2.1.2/media/images/__init__.py",
    "frontend/static/TableTools-2.1.2/media/images/psd/collection.psd",
    "frontend/static/TableTools-2.1.2/media/images/psd/file_types.psd",
    "frontend/static/TableTools-2.1.2/media/images/psd/__init__.py",
    "frontend/static/TableTools-2.1.2/media/images/psd/printer.psd",
    "frontend/static/TableTools-2.1.2/media/images/psd/copy document.psd",
    "frontend/static/TableTools-2.1.2/media/images/print_hover.png",
    "frontend/static/TableTools-2.1.2/media/images/csv_hover.png",
    "frontend/static/TableTools-2.1.2/media/images/background.png",
    "frontend/static/TableTools-2.1.2/media/images/copy.png",
    "frontend/static/TableTools-2.1.2/media/images/pdf.png",
    "frontend/static/TableTools-2.1.2/media/images/pdf_hover.png",
    "frontend/static/TableTools-2.1.2/media/images/copy_hover.png",
    "frontend/static/TableTools-2.1.2/media/images/xls.png",
    "frontend/static/TableTools-2.1.2/media/images/xls_hover.png",
    "frontend/static/TableTools-2.1.2/media/images/csv.png",
    "frontend/static/TableTools-2.1.2/media/as3/__init__.py",
    "frontend/static/TableTools-2.1.2/media/as3/ZeroClipboard.as",
    "frontend/static/TableTools-2.1.2/media/as3/ZeroClipboardPdf.as",
    "frontend/static/TableTools-2.1.2/pdf_message.html",
    "frontend/static/TableTools-2.1.2/index.html",
    "frontend/static/TableTools-2.1.2/__init__.py",
    "frontend/static/TableTools-2.1.2/tabs.html",
    "frontend/static/TableTools-2.1.2/swf_path.html",
    "frontend/static/TableTools-2.1.2/defaults.html",
    "frontend/static/TableTools-2.1.2/collection.html",
    "frontend/static/TableTools-2.1.2/multi_instance.html",
    "frontend/static/TableTools-2.1.2/alt_init.html",
    "frontend/static/TableTools-2.1.2/plug-in.html",
    "frontend/static/TableTools-2.1.2/multiple_tables.html",
    "frontend/static/TableTools-2.1.2/alter_buttons.html",
    "frontend/static/TableTools-2.1.2/select_multi.html",
    "frontend/static/TableTools-2.1.2/bootstrap.html",
    "frontend/static/TableTools-2.1.2/theme.html",
    "frontend/static/TableTools-2.1.2/select_single.html",
    "frontend/static/jui/jquery-ui-1.8.12.custom/css/smoothness/images/ui-bg_glass_75_e6e6e6_1x400.png",
    "frontend/static/jui/jquery-ui-1.8.12.custom/css/smoothness/images/ui-icons_454545_256x240.png",
    "frontend/static/jui/jquery-ui-1.8.12.custom/css/smoothness/images/ui-bg_flat_75_ffffff_40x100.png",
    "frontend/static/jui/jquery-ui-1.8.12.custom/css/smoothness/images/ui-icons_cd0a0a_256x240.png",
    "frontend/static/jui/jquery-ui-1.8.12.custom/css/smoothness/images/ui-bg_flat_0_aaaaaa_40x100.png",
    "frontend/static/jui/jquery-ui-1.8.12.custom/css/smoothness/images/ui-bg_glass_65_ffffff_1x400.png",
    "frontend/static/jui/jquery-ui-1.8.12.custom/css/smoothness/images/ui-bg_highlight-soft_75_cccccc_1x100.png",
    "frontend/static/jui/jquery-ui-1.8.12.custom/css/smoothness/images/ui-icons_2e83ff_256x240.png",
    "frontend/static/jui/jquery-ui-1.8.12.custom/css/smoothness/images/ui-bg_glass_75_dadada_1x400.png",
    "frontend/static/jui/jquery-ui-1.8.12.custom/css/smoothness/images/ui-icons_888888_256x240.png",
    "frontend/static/jui/jquery-ui-1.8.12.custom/css/smoothness/images/ui-bg_glass_55_fbf9ee_1x400.png",
    "frontend/static/jui/jquery-ui-1.8.12.custom/css/smoothness/images/ui-bg_glass_95_fef1ec_1x400.png",
    "frontend/static/jui/jquery-ui-1.8.12.custom/css/smoothness/images/ui-icons_222222_256x240.png",
    "frontend/static/jui/jquery-ui-1.8.12.custom/css/smoothness/jquery-ui-1.8.12.custom.css",
    "frontend/static/jui/jquery-ui-1.8.12.custom/index.html",
    "frontend/static/jui/jquery-ui-1.8.12.custom/js/jquery-1.5.1.min.js",
    "frontend/static/jui/jquery-ui-1.8.12.custom/js/jquery-ui-1.8.12.custom.min.js",
    "frontend/static/as3/ZeroClipboard.as",
    "frontend/static/as3/ZeroClipboardPdf.as",
    "frontend/media/__init__.py",
    "frontend/media/swf/copy_csv_xls_pdf.swf",
    "frontend/media/swf/__init__.py",
    "frontend/media/swf/copy_csv_xls.swf",
    "frontend/templates/index.js",
    "frontend/templates/enrichment.html",
    "frontend/templates/index.mako",
    "frontend/templates/index.html",
    "frontend/templates/__init__.py",
    "frontend/templates/cite.mako",
    "frontend/templates/news.mako",
    "frontend/templates/enrichment_not_ready.html",
    "frontend/templates/results.js",
    "frontend/templates/roadmap.mako",
    "frontend/templates/results.mako",
    "frontend/templates/gfs.php",
    "frontend/templates/results.html",
    "frontend/templates/master.mako",
    "frontend/templates/demo.mako",
    "frontend/templates/help.mako",
    "frontend/templates/overview.mako",
    "frontend/__init__.py",
    ],
    },
    scripts=[os.path.join(r,f) for r,d,fs in os.walk("grsnp/bin") for f in fs if f.endswith(".py") or f.endswith(".sh") or "bedToBigBed" in f],
    url='http://www.genomerunner.org',
    license='LICENSE.txt',
    install_requires=[
    "cython",
    "pybedtools",
    "bx-python",
    "rpy2",
    "mako",
    "simplejson",
    ],
    description='GenomeRunner Web: Functional interpretation of SNPs within epigenomic context',
    long_description=open('README.rst').read(),
    cmdclass={
        'install': CustomInstallCommand,
        'develop': CustomDevelopCommand
    })