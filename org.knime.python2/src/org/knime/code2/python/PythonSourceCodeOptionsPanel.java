/*
 * ------------------------------------------------------------------------
 *  Copyright by KNIME GmbH, Konstanz, Germany
 *  Website: http://www.knime.org; Email: contact@knime.org
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License, Version 3, as
 *  published by the Free Software Foundation.
 *
 *  This program is distributed in the hope that it will be useful, but
 *  WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program; if not, see <http://www.gnu.org/licenses>.
 *
 *  Additional permission under GNU GPL version 3 section 7:
 *
 *  KNIME interoperates with ECLIPSE solely via ECLIPSE's plug-in APIs.
 *  Hence, KNIME and ECLIPSE are both independent programs and are not
 *  derived from each other. Should, however, the interpretation of the
 *  GNU GPL Version 3 ("License") under any applicable laws result in
 *  KNIME and ECLIPSE being a combined program, KNIME GMBH herewith grants
 *  you the additional permission to use and propagate KNIME together with
 *  ECLIPSE with only the license terms in place for ECLIPSE applying to
 *  ECLIPSE and the GNU GPL Version 3 applying for KNIME, provided the
 *  license terms of ECLIPSE themselves allow for the respective use and
 *  propagation of ECLIPSE together with KNIME.
 *
 *  Additional permission relating to nodes for KNIME that extend the Node
 *  Extension (and in particular that are based on subclasses of NodeModel,
 *  NodeDialog, and NodeView) and that only interoperate with KNIME through
 *  standard APIs ("Nodes"):
 *  Nodes are deemed to be separate and independent programs and to not be
 *  covered works.  Notwithstanding anything to the contrary in the
 *  License, the License does not apply to Nodes, you are not required to
 *  license Nodes under the License, and you are granted a license to
 *  prepare and propagate Nodes, in each case even if such Nodes are
 *  propagated with or for interoperation with KNIME.  The owner of a Node
 *  may freely choose the license terms applicable to such Node, including
 *  when such Node is propagated with or for interoperation with KNIME.
 * ------------------------------------------------------------------------
 */

package org.knime.code2.python;

import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.GridLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.BorderFactory;
import javax.swing.ButtonGroup;
import javax.swing.JCheckBox;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JRadioButton;
import javax.swing.JTextField;
import javax.swing.event.DocumentEvent;
import javax.swing.event.DocumentListener;

import org.knime.code2.generic.SourceCodeOptionsPanel;
import org.knime.python2.extensions.serializationlibrary.SentinelOption;
import org.knime.python2.kernel.PythonKernelOptions;

/**
 * The options panel for every node concerned with python scripting.
 * 
 * @author Clemens von Schwerin, KNIME.com, Konstanz, Germany
 *
 */

public class PythonSourceCodeOptionsPanel extends SourceCodeOptionsPanel<PythonSourceCodePanel, PythonSourceCodeConfig> {
	
	private static final long serialVersionUID = -5612311503547573497L;
	private ButtonGroup m_pythonVersion;
	private JRadioButton m_python2;
	private JRadioButton m_python3;
	
	private JCheckBox m_convertToPython;
	private JCheckBox m_convertFromPython;
	private ButtonGroup m_sentinelValueGroup;
	private JRadioButton m_minVal;
	private JRadioButton m_maxVal;
	private JRadioButton m_useInput;
	private JTextField m_sentinelInput;
	private JLabel m_missingWarningLabel;
	private int m_sentinelValue;

	public PythonSourceCodeOptionsPanel(PythonSourceCodePanel sourceCodePanel) {
		super(sourceCodePanel);
	}
	
	@Override
	protected JPanel getAdditionalOptionsPanel() {
		m_pythonVersion = new ButtonGroup();
		m_python2 = new JRadioButton("Python 2");
		m_python3 = new JRadioButton("Python 3");
		m_pythonVersion.add(m_python2);
		m_pythonVersion.add(m_python3);
		PythonKernelOptionsListener pkol = new PythonKernelOptionsListener();
		m_python2.addActionListener(pkol);
		m_python3.addActionListener(pkol);
		JPanel panel = new JPanel(new GridBagLayout());
		GridBagConstraints gbc = new GridBagConstraints();
		gbc.insets = new Insets(5, 5, 5, 5);
		gbc.anchor = GridBagConstraints.NORTHWEST;
		gbc.fill = GridBagConstraints.BOTH;
		gbc.weightx = 0;
		gbc.weighty = 0;
		gbc.gridx = 0;
		gbc.gridy = 0;
		JPanel versionPanel = new JPanel(new FlowLayout());
		versionPanel.setBorder(BorderFactory.createTitledBorder("Use Python Version"));
		versionPanel.add(m_python2);
		versionPanel.add(m_python3);
		panel.add(versionPanel, gbc);
		//Missing value handling for Int and Long
		JPanel missingPanel = new JPanel(new GridLayout(0,1));
		missingPanel.setBorder(BorderFactory.createTitledBorder("Missing Values (Int, Long)"));
		m_convertToPython = new JCheckBox("convert missing values to sentinel value (to python)");
		m_convertToPython.addActionListener(pkol);
		missingPanel.add(m_convertToPython);
		m_convertFromPython = new JCheckBox("convert sentinel values to missing value (from python)");
		m_convertFromPython.addActionListener(pkol);
		missingPanel.add(m_convertFromPython);
		JPanel sentinelPanel = new JPanel(new FlowLayout());
		JLabel sentinelLabel = new JLabel("Sentinel value: ");
		m_sentinelValueGroup = new ButtonGroup();
		m_minVal = new JRadioButton("MIN_VAL");
		m_minVal.addActionListener(pkol);
		m_maxVal = new JRadioButton("MAX_VAL");
		m_maxVal.addActionListener(pkol);
		m_useInput = new JRadioButton("");
		m_useInput.addActionListener(pkol);
		m_sentinelValueGroup.add(m_minVal);
		m_sentinelValueGroup.add(m_maxVal);
		m_sentinelValueGroup.add(m_useInput);
		m_minVal.setSelected(true);
		//TODO enable only if radio button is enabled
		m_sentinelValue = 0;
		m_sentinelInput = new JTextField("0");
		m_sentinelInput.setPreferredSize(new Dimension(70, m_sentinelInput.getPreferredSize().height));
		m_sentinelInput.getDocument().addDocumentListener(new DocumentListener() {
			
			@Override
			public void removeUpdate(DocumentEvent e) {
				updateSentinelValue();
				getSourceCodePanel().setKernelOptions(m_python3.isSelected(), m_convertToPython.isSelected(),
						m_convertFromPython.isSelected(), getSelectedSentinelOption(), m_sentinelValue);
			}
			
			@Override
			public void insertUpdate(DocumentEvent e) {
				updateSentinelValue();
				getSourceCodePanel().setKernelOptions(m_python3.isSelected(), m_convertToPython.isSelected(),
						m_convertFromPython.isSelected(), getSelectedSentinelOption(), m_sentinelValue);
			}
			
			@Override
			public void changedUpdate(DocumentEvent e) {
				//does not get fired
			}
		});
		sentinelPanel.add(sentinelLabel);
		sentinelPanel.add(m_minVal);
		sentinelPanel.add(m_maxVal);
		sentinelPanel.add(m_useInput);
		sentinelPanel.add(m_sentinelInput);
		missingPanel.add(sentinelPanel);
		m_missingWarningLabel = new JLabel("");
		missingPanel.add(m_missingWarningLabel);
		gbc.gridx = 0;
		gbc.gridy++;
		panel.add(missingPanel, gbc);
		
		return panel;
	}
	
	@Override
	public void loadSettingsFrom(PythonSourceCodeConfig config) {
		super.loadSettingsFrom(config);
		PythonKernelOptions kopts = config.getKernelOptions();
		if (kopts.getUsePython3()) {
			m_python3.setSelected(true);
		} else {
			m_python2.setSelected(true);
		}
		//Missing value handling
		m_convertToPython.setSelected(kopts.getConvertMissingToPython());
		m_convertFromPython.setSelected(kopts.getConvertMissingFromPython());
		if(kopts.getSentinelOption() == SentinelOption.MIN_VAL) {
			m_minVal.setSelected(true);
		} else if(kopts.getSentinelOption() == SentinelOption.MAX_VAL) {
			m_maxVal.setSelected(true);
		} else {
			m_useInput.setSelected(true);
		}
		m_sentinelInput.setText(kopts.getSentinelValue() + "");
		m_sentinelValue = kopts.getSentinelValue();
		getSourceCodePanel().setKernelOptions(m_python3.isSelected(), m_convertToPython.isSelected(),
				m_convertFromPython.isSelected(), getSelectedSentinelOption(), m_sentinelValue);
	}
	
	@Override
	public void saveSettingsTo(PythonSourceCodeConfig config) {
		super.saveSettingsTo(config);
		config.setKernelOptions(m_python3.isSelected(), m_convertToPython.isSelected(),
					m_convertFromPython.isSelected(), getSelectedSentinelOption(), m_sentinelValue);
	}
	
	private void updateSentinelValue()
	{
		try {
			m_sentinelValue = Integer.parseInt(m_sentinelInput.getText());
			m_missingWarningLabel.setText("");
		} catch(NumberFormatException ex) {
			m_sentinelValue = 0;
			m_missingWarningLabel.setText("<html><font color=\"red\"><b>Sentinel value cannot be parsed. <br /> Default value 0 is used instead!</b></font></html>");
		}
	}
	
	private SentinelOption getSelectedSentinelOption()
	{
		SentinelOption so = SentinelOption.MIN_VAL;
		if(m_minVal.isSelected()) {
			so = SentinelOption.MIN_VAL;
		} else if(m_maxVal.isSelected()) {
			so = SentinelOption.MAX_VAL;
		} else if(m_useInput.isSelected()) {
			so = SentinelOption.CUSTOM;
		}
		return so;
	}
	
	private class PythonKernelOptionsListener implements ActionListener {

		@Override
		public void actionPerformed(ActionEvent e) {
			
			getSourceCodePanel().setKernelOptions(m_python3.isSelected(), m_convertToPython.isSelected(),
					m_convertFromPython.isSelected(), getSelectedSentinelOption(), m_sentinelValue);
			
		}
		
	}

}